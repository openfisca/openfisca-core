# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import

import numpy as np

from openfisca_core.simulations import Simulation


def _get_person_count(input_dict):
    first_value = next(iter(input_dict.values()))
    if isinstance(first_value, dict):
        first_value = next(iter(first_value.values()))

    if not isinstance(first_value, list):
        return 1
    return len(first_value)


class SimulationBuilder(object):

    def __init__(self, tax_benefit_system):
        self.tax_benefit_system = tax_benefit_system
        self.entities_plural = [entity.plural for entity in self.tax_benefit_system.entities]
        self.entities_by_singular = {entity.key: entity for entity in self.tax_benefit_system.entities}

    def build_from_dict(self, input_dict, **kwargs):
        """
            Build a simulation from a Python dict ``input_dict``
        """

        if not input_dict:
            return self.build_default_simulation(**kwargs)
        input_dict = self.explicit_singular_entities(input_dict)
        if all(key in self.entities_plural for key in input_dict.keys()):
            return Simulation(self.tax_benefit_system, input_dict, **kwargs)
        else:
            return self.build_from_variables(input_dict, **kwargs)

    def build_from_variables(self, input_dict, default_period = None, **kwargs):
        """
            Build a simulation from a Python dict ``input_dict`` describing variables values without expliciting entities.

            This method uses :any:`build_default_simulation` to infer an entity structure

            Example:

            >>> simulation_builder.build_from_variables(
                {'salary': {'2016-10': 12000}}
                )
        """
        count = _get_person_count(input_dict)
        simulation = self.build_default_simulation(count, **kwargs)
        for variable, value in input_dict.items():
            if not isinstance(value, dict):
                simulation.set_input(variable, default_period, value)
            else:
                for period, dated_value in value.items():
                    simulation.set_input(variable, period, dated_value)
        return simulation

    def build_default_simulation(self, count = 1, **kwargs):
        """
            Build a simulation where:
                - There are ``count`` persons
                - There are ``count`` instances of each group entity, containing one person
                - Every person has, in each entity, the first role
        """

        simulation = Simulation(self.tax_benefit_system, **kwargs)
        for entity in simulation.entities.values():
            entity.count = count
            entity.ids = np.array(range(count))
            if not entity.is_person:
                entity.members_entity_id = entity.ids  # Each person is its own group entity
                entity.members_role = entity.filled_array(entity.flattened_roles[0])
        return simulation

    def explicit_singular_entities(self, input_dict):
        """
            Preprocess ``input_dict`` to explicit entities defined using the single-entity shortcut

            Example:

            >>> simulation_builder.explicit_singular_entities(
                {'persons': {'Javier': {}}, 'household': {'parents': ['Alicia']}}
                )
            >>>
            >>> {'persons': {'Javier': {}}, 'households': {'household': {'parents': ['Alicia']}}
        """

        singular_keys = set(input_dict).intersection(self.entities_by_singular)
        if not singular_keys:
            return input_dict

        result = {
            entity_id: entity_description
            for (entity_id, entity_description) in input_dict.items()
            if entity_id in self.entities_plural
            }  # filter out the singular entities

        for singular in singular_keys:
            plural = self.entities_by_singular[singular].plural
            result[plural] = {singular: input_dict[singular]}

        return result
