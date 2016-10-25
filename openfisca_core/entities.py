# -*- coding: utf-8 -*-

import numpy as np
import warnings

from enumerations import Enum


class Entity(object):
    key = None
    plural = None
    label = None
    roles = None
    is_person = False

    def __init__(self, simulation):
        self.simulation = simulation
        self.count = 0
        self.step_size = 0

    # Calculations

    def check_variable_defined_for_entity(self, variable_name):
        if not (self.simulation.get_variable_entity(variable_name) == self):
            variable_entity = self.simulation.get_variable_entity(variable_name)
            raise Exception(
                "Variable {} is not defined for {} but for {}".format(
                    variable_name, self.key, variable_entity.key)
                )
    def calculate(self, variable_name, period = None):
        self.check_variable_defined_for_entity(variable_name)
        return self.simulation.calculate(variable_name, period)

    def calculate_add(self, variable_name, period = None):
        self.check_variable_defined_for_entity(variable_name)
        return self.simulation.calculate_add(variable_name, period)

    def calculate_divide(self, variable_name, period = None):
        self.check_variable_defined_for_entity(variable_name)
        return self.simulation.calculate_divide(variable_name, period)

    def calculate_add_divide(self, variable_name, period = None):
        self.check_variable_defined_for_entity(variable_name)
        return self.simulation.calculate_add_divide(variable_name, period)
class PersonEntity(Entity):
    is_person = True

    # Projection person -> person

    def role_in(self, entity):
        entity = self.simulation.get_entity(entity)
        return entity.members_role
class GroupEntity(Entity):

    @classmethod
    def get_role_enum(cls):
        return Enum(map(lambda role: role['key'], cls.roles))

    def __init__(self, simulation):
        Entity.__init__(self, simulation)
        self.members_entity_id = None
        self.members_role = None
        self.members_legacy_role = None
        self.members_position = None

    @property
    def members(self):
        return self.simulation.persons
        else:





