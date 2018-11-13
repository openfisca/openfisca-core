# -*- coding: utf-8 -*-


from __future__ import unicode_literals, print_function, division, absolute_import

from openfisca_core.simulations import Simulation


class SimulationBuilder(object):

    def __init__(self, tax_benefit_system):
        self.tax_benefit_system = tax_benefit_system
        self.default_simulation_json = {
            entity.plural: {
                '_': {} if entity.is_person else {
                    entity.roles[0].plural or entity.roles[0].key : ['_']
                }}
            for entity in self.tax_benefit_system.entities
            }

    def build_from_dict(self, input_dict, default_period = None):
        entities_plural = [entity.plural for entity in self.tax_benefit_system.entities]
        if all(key in entities_plural for key in input_dict.keys()):
            return Simulation(self.tax_benefit_system, input_dict, default_period = default_period)
        else:
            return self.build_from_variables(input_dict, default_period)

    def build_from_variables(self, input_dict, default_period = None):
        simulation = Simulation(self.tax_benefit_system, self.default_simulation_json)
        for variable, value in input_dict.items():
            if not isinstance(value, dict):
                simulation.set_input(variable, default_period, value)
            else:
                for period, dated_value in value.items():
                    simulation.set_input(variable, period, dated_value)
        return simulation
