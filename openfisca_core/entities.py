# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Founœdation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from .tools import empty_clone


class AbstractEntity(object):
    column_by_name = None  # Class attribute. Must be overridden by subclasses with an OrderedDict.
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
