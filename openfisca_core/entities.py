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
        else:





