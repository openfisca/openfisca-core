# -*- coding: utf-8 -*-


from .tools import empty_clone


class AbstractEntity(object):
    count = 0
    key_plural = None
    key_singular = None
    index_for_person_variable_name = None  # Class attribute. Not used for persons
    is_persons_entity = False  # Class attribute

    # Maximum number of different roles in the entity.
    # Ex : If the biggest family have 7 members, roles_count = 7 for the entity family.
    # Not relevant for a person
    roles_count = None

    role_for_person_variable_name = None  # Class attribute. Not used for persons
    step_size = 0
    simulation = None
    symbol = None  # Class attribute. Must be overridden by subclasses.

    def __init__(self, simulation = None):
        if self.is_persons_entity:
            assert self.index_for_person_variable_name is None
            assert self.role_for_person_variable_name is None
        else:
            assert self.index_for_person_variable_name is not None
            assert self.role_for_person_variable_name is not None
        if simulation is not None:
            self.simulation = simulation

    def clone(self, simulation):
        """Copy the entity just enough to be able to run the simulation without modifying the original simulation."""
        new = empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.iteritems():
            if key != 'simulation':
                new_dict[key] = value

        new_dict['simulation'] = simulation

        return new

    def iter_member_persons_role_and_id(self, member):
        assert not self.is_persons_entity
        raise NotImplementedError('Method "iter_member_persons_role_and_id" is not implemented for class {}'.format(
            self.__class__.__name__))
