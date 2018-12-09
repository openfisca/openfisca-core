# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import

import dpath
import numpy as np

from openfisca_core.commons import basestring_type
from openfisca_core.errors import VariableNotFound, SituationParsingError, PeriodMismatchError
from openfisca_core.periods import key_period_size, period as make_period
from openfisca_core.simulations import Simulation


class SimulationBuilder(object):

    def __init__(self):
        self.input_buffer = {}
        self.entity_counts = {}
        self.entity_ids = {}
        self.memberships = {}
        self.roles = {}

    def build_from_dict(self, tax_benefit_system, input_dict, default_period = None, **kwargs):
        """
            Build a simulation from ``input_dict``

            This method uses :any:`build_from_entities` if entities are fully specified, or :any:`build_from_variables` if not.

            :param dict input_dict: A dict represeting the input of the simulation
            :param default_period: If provided, inputs variables without an explicit period will be set for ``default_period``
            :param kwargs: Same keywords argument than the :any:`Simulation` constructor
            :return: A :any:`Simulation`
        """

        input_dict = self.explicit_singular_entities(tax_benefit_system, input_dict)
        if all(key in tax_benefit_system.entities_plural() for key in input_dict.keys()):
            return self.build_from_entities(tax_benefit_system, input_dict, default_period, **kwargs)
        else:
            return self.build_from_variables(tax_benefit_system, input_dict, default_period, **kwargs)

    def build_from_entities(self, tax_benefit_system, input_dict, default_period = None, **kwargs):
        """
            Build a simulation from a Python dict ``input_dict`` fully specifying entities.

            Examples:

            >>> simulation_builder.build_from_entities({
                'persons': {'Javier': { 'salary': {'2018-11': 2000}}},
                'households': {'household': {'parents': ['Javier']}}
                })
        """
        simulation = kwargs.pop('simulation', None)  # Only for backward compatibility with previous Simulation constructor
        if simulation is None:
            simulation = Simulation(tax_benefit_system, **kwargs)

        check_type(input_dict, dict, ['error'])
        unexpected_entities = [entity for entity in input_dict if entity not in tax_benefit_system.entities_plural()]
        if unexpected_entities:
            unexpected_entity = unexpected_entities[0]
            raise SituationParsingError([unexpected_entity],
                ''.join([
                    "Some entities in the situation are not defined in the loaded tax and benefit system.",
                    "These entities are not found: {0}.",
                    "The defined entities are: {1}."]
                    )
                .format(
                ', '.join(unexpected_entities),
                ', '.join(tax_benefit_system.entities_plural())
                    )
                )
        persons_json = input_dict.get(tax_benefit_system.person_entity.plural, None)

        if not persons_json:
            raise SituationParsingError([tax_benefit_system.person_entity.plural],
                'No {0} found. At least one {0} must be defined to run a simulation.'.format(tax_benefit_system.person_entity.key))

        persons_ids = self.add_person_entity(simulation.persons, persons_json, default_period = default_period)
        try:
            self.finalize_variables_init(simulation.persons)
        except PeriodMismatchError as e:
            self.raise_period_mismatch(simulation.persons, persons_json, e)

        for entity_class in tax_benefit_system.group_entities:
            entity = simulation.entities[entity_class.key]
            instances_json = input_dict.get(entity_class.plural)
            self.add_group_entity(simulation.persons.plural, persons_ids, entity, instances_json, default_period = default_period)

        return simulation

    def build_from_variables(self, tax_benefit_system, input_dict, default_period = None, **kwargs):
        """
            Build a simulation from a Python dict ``input_dict`` describing variables values without expliciting entities.

            This method uses :any:`build_default_simulation` to infer an entity structure

            Example:

            >>> simulation_builder.build_from_variables(
                {'salary': {'2016-10': 12000}}
                )
        """
        count = _get_person_count(input_dict)
        simulation = self.build_default_simulation(tax_benefit_system, count, **kwargs)
        for variable, value in input_dict.items():
            if not isinstance(value, dict):
                simulation.set_input(variable, default_period, value)
            else:
                for period, dated_value in value.items():
                    simulation.set_input(variable, period, dated_value)
        return simulation

    def build_default_simulation(self, tax_benefit_system, count = 1, **kwargs):
        """
            Build a simulation where:
                - There are ``count`` persons
                - There are ``count`` instances of each group entity, containing one person
                - Every person has, in each entity, the first role
        """

        simulation = Simulation(tax_benefit_system, **kwargs)
        for entity in simulation.entities.values():
            entity.count = count
            entity.ids = np.array(range(count))
            if not entity.is_person:
                entity.members_entity_id = entity.ids  # Each person is its own group entity
                entity.members_role = entity.filled_array(entity.flattened_roles[0])
        return simulation

    def explicit_singular_entities(self, tax_benefit_system, input_dict):
        """
            Preprocess ``input_dict`` to explicit entities defined using the single-entity shortcut

            Example:

            >>> simulation_builder.explicit_singular_entities(
                {'persons': {'Javier': {}, }, 'household': {'parents': ['Javier']}}
                )
            >>> {'persons': {'Javier': {}}, 'households': {'household': {'parents': ['Javier']}}
        """

        singular_keys = set(input_dict).intersection(tax_benefit_system.entities_by_singular())
        if not singular_keys:
            return input_dict

        result = {
            entity_id: entity_description
            for (entity_id, entity_description) in input_dict.items()
            if entity_id in tax_benefit_system.entities_plural()
            }  # filter out the singular entities

        for singular in singular_keys:
            plural = tax_benefit_system.entities_by_singular()[singular].plural
            result[plural] = {singular: input_dict[singular]}

        return result

    def add_person_entity(self, entity, instances_json, default_period = None):
        """
            Add the simulation's instances of the persons entity as described in ``instances_json``.
        """
        check_type(instances_json, dict, [entity.plural])
        self.entity_counts[entity.plural] = len(instances_json)
        self.entity_ids[entity.plural] = list(instances_json.keys())

        for instance_id, instance_object in instances_json.items():
            check_type(instance_object, dict, [entity.plural, instance_id])
            self.init_variable_values(entity, instance_object, str(instance_id), default_period = default_period)

        return self.get_ids(entity.plural)

    def add_group_entity(self, persons_plural, persons_ids, entity, instances_json, default_period = None):
        """
            Add all instances of one of the model's entities as described in ``instances_json``.
        """
        persons_count = len(persons_ids)
        persons_to_allocate = set(persons_ids)

        check_type(instances_json, dict, [entity.plural])
        entity_ids = list(instances_json.keys())
        self.entity_ids[entity.plural] = entity_ids
        self.entity_counts[entity.plural] = len(entity_ids)
        self.memberships[entity.plural] = np.empty(persons_count, dtype = np.int32)
        self.roles[entity.plural] = np.empty(persons_count, dtype = object)

        for instance_id, instance_object in instances_json.items():
            check_type(instance_object, dict, [entity.plural, instance_id])

            variables_json = instance_object.copy()  # Don't mutate function input

            roles_json = {
                role.plural or role.key: clean_person_list(variables_json.pop(role.plural or role.key, []))
                for role in entity.roles
                }

            for role_id, role_definition in roles_json.items():
                check_type(role_definition, list, [entity.plural, instance_id, role_id])
                for index, person_id in enumerate(role_definition):
                    entity_plural = entity.plural
                    self.check_persons_to_allocate(persons_plural, entity_plural,
                                                   persons_ids,
                                                   person_id, instance_id, role_id,
                                                   persons_to_allocate, index)

                    persons_to_allocate.discard(person_id)

            entity_index = entity_ids.index(instance_id)
            for person_role, person_id in iter_over_entity_members(entity, roles_json):
                person_index = persons_ids.index(person_id)
                self.memberships[entity.plural][person_index] = entity_index
                self.roles[entity.plural][person_index] = person_role

            self.init_variable_values(entity, variables_json, instance_id, default_period = default_period)

        if persons_to_allocate:
            raise SituationParsingError([entity.plural],
                '{0} have been declared in {1}, but are not members of any {2}. All {1} must be allocated to a {2}.'.format(
                    persons_to_allocate, persons_plural, entity.key)
                )

        try:
            self.finalize_variables_init(entity)
        except PeriodMismatchError as e:
            self.raise_period_mismatch(entity, instances_json, e)

    def get_input(self, variable, period):
        return self.input_buffer[variable][period]

    def check_persons_to_allocate(self, persons_plural, entity_plural,
                                  persons_ids,
                                  person_id, entity_id, role_id,
                                  persons_to_allocate, index):
        check_type(person_id, basestring_type, [entity_plural, entity_id, role_id, str(index)])
        if person_id not in persons_ids:
            raise SituationParsingError([entity_plural, entity_id, role_id],
                "Unexpected value: {0}. {0} has been declared in {1} {2}, but has not been declared in {3}.".format(
                    person_id, entity_id, role_id, persons_plural)
                )
        if person_id not in persons_to_allocate:
            raise SituationParsingError([entity_plural, entity_id, role_id],
                "{} has been declared more than once in {}".format(
                    person_id, entity_plural)
                )

    def init_variable_values(self, entity, instance_object, instance_id, default_period = None):
        for variable_name, variable_values in instance_object.items():
            path_in_json = [entity.plural, instance_id, variable_name]
            try:
                entity.check_variable_defined_for_entity(variable_name)
            except ValueError as e:  # The variable is defined for another entity
                raise SituationParsingError(path_in_json, e.args[0])
            except VariableNotFound as e:  # The variable doesn't exist
                raise SituationParsingError(path_in_json, e.message, code = 404)

            if entity.plural in self.entity_ids and instance_id in self.get_ids(entity.plural):
                instance_index = self.get_ids(entity.plural).index(instance_id)
            else:
                instance_index = entity.ids.index(instance_id)

            if not isinstance(variable_values, dict):
                if default_period is None:
                    raise SituationParsingError(path_in_json,
                        "Can't deal with type: expected object. Input variables should be set for specific periods. For instance: {'salary': {'2017-01': 2000, '2017-02': 2500}}, or {'birth_date': {'ETERNITY': '1980-01-01'}}.")
                variable_values = {default_period: variable_values}

            for period, value in variable_values.items():
                try:
                    make_period(period)
                except ValueError as e:
                    raise SituationParsingError(path_in_json, e.args[0])
                variable = entity.get_variable(variable_name)
                self.add_variable_value(entity, variable, instance_index, instance_id, period, value)

    def add_variable_value(self, entity, variable, instance_index, instance_id, period_str, value):
        path_in_json = [entity.plural, instance_id, variable.name, period_str]

        if value is None:
            return

        if variable.name not in self.input_buffer:
            self.input_buffer[variable.name] = {}
        array = self.input_buffer[variable.name].get(str(period_str))

        if array is None:
            array_size = self.get_count(entity.plural) if entity.plural in self.entity_counts else entity.count
            array = variable.default_array(array_size)

        try:
            value = variable.check_set_value(value)
        except ValueError as error:
            raise SituationParsingError(path_in_json, *error.args)

        array[instance_index] = value

        self.input_buffer[variable.name][str(period_str)] = array

    def finalize_variables_init(self, entity):
        # Due to set_input mechanism, we must bufferize all inputs, then actually set them,
        # so that the months are set first and the years last.
        if entity.plural in self.entity_counts:
            entity.count = self.get_count(entity.plural)
            entity.ids = self.get_ids(entity.plural)
        if entity.plural in self.memberships:
            entity.members_entity_id = self.get_memberships(entity.plural)
            entity.members_role = self.get_roles(entity.plural)
        for variable_name in self.input_buffer.keys():
            try:
                holder = entity.get_holder(variable_name)
            except ValueError:  # Wrong entity, we can just ignore that
                continue
            buffer = self.input_buffer[variable_name]
            periods = [make_period(period_str) for period_str in self.input_buffer[variable_name].keys()]
            # We need to handle small periods first for set_input to work
            sorted_periods = sorted(periods, key=key_period_size)
            for period in sorted_periods:
                array = buffer[str(period)]
                holder.set_input(period, array)

    def raise_period_mismatch(self, entity, json, e):
        # This error happens when we try to set a variable value for a period that doesn't match its definition period
        # It is only raised when we consume the buffer. We thus don't know which exact key caused the error.
        # We do a basic research to find the culprit path
        culprit_path = next(
            dpath.search(json, "*/{}/{}".format(e.variable_name, str(e.period)), yielded = True),
            None)
        if culprit_path:
            path = [entity.plural] + culprit_path[0].split('/')
        else:
            path = [entity.plural]  # Fallback: if we can't find the culprit, just set the error at the entities level

        raise SituationParsingError(path, e.message)

    def get_count(self, entity_name):
        return self.entity_counts[entity_name]

    def get_ids(self, entity_name):
        return self.entity_ids[entity_name]

    def get_memberships(self, entity_name):
        return self.memberships[entity_name]

    def get_roles(self, entity_name):
        return self.roles[entity_name]


def check_type(input, input_type, path = []):
    json_type_map = {
        dict: "Object",
        list: "Array",
        basestring_type: "String",
        }
    if not isinstance(input, input_type):
        raise SituationParsingError(path,
            "Invalid type: must be of type '{}'.".format(json_type_map[input_type]))


def clean_person_list(data):
    if isinstance(data, (str, int)):
        data = [data]
    if isinstance(data, list):
        return [str(item) if isinstance(item, int) else item for item in data]
    return data


def iter_over_entity_members(entity_description, scenario_entity):
    # One by one, yield individu_role, individy_legacy_role, individu_id
    legacy_role_i = 0
    for role in entity_description.roles:
        role_name = role.plural or role.key
        individus = scenario_entity.get(role_name)

        if individus:
            if not type(individus) == list:
                individus = [individus]

            legacy_role_j = 0
            for individu in individus:
                if role.subroles:
                    yield role.subroles[legacy_role_j], individu
                else:
                    yield role, individu
                legacy_role_j += 1
        legacy_role_i += (role.max or 1)


def _get_person_count(input_dict):
    try:
        first_value = next(iter(input_dict.values()))
        if isinstance(first_value, dict):
            first_value = next(iter(first_value.values()))
        if isinstance(first_value, basestring_type):
            return 1

        return len(first_value)
    except Exception:
        return 1
