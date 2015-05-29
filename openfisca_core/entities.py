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
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from . import holders
from .tools import empty_clone


class AbstractEntity(object):
    column_by_name = None  # Class attribute. Must be overridden by subclasses with an OrderedDict.
    count = 0
    holder_by_name = None
    key_plural = None
    key_singular = None
    index_for_person_variable_name = None  # Class attribute. Not used for persons
    is_persons_entity = False  # Class attribute
    roles_count = None  # Not used for persons
    role_for_person_variable_name = None  # Class attribute. Not used for persons
    step_size = 0
    simulation = None
    symbol = None  # Class attribute. Must be overridden by subclasses.

    def __init__(self, simulation = None):
        self.holder_by_name = {}
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
            if key not in ('holder_by_name', 'simulation'):
                new_dict[key] = value

        new_dict['simulation'] = simulation
        # Caution: holders must be cloned after the simulation has been set into new.
        new_dict['holder_by_name'] = {
            name: holder.clone(new)
            for name, holder in self.holder_by_name.iteritems()
            }

        return new

    def compute(self, column_name, period = None, accept_other_period = False, requested_formulas_by_period = None):
        return self.get_or_new_holder(column_name).compute(period = period, accept_other_period = accept_other_period,
            requested_formulas_by_period = requested_formulas_by_period)

    def compute_add(self, column_name, period = None, requested_formulas_by_period = None):
        return self.get_or_new_holder(column_name).compute_add(period = period,
            requested_formulas_by_period = requested_formulas_by_period)

    def compute_add_divide(self, column_name, period = None, requested_formulas_by_period = None):
        return self.get_or_new_holder(column_name).compute_add_divide(period = period,
            requested_formulas_by_period = requested_formulas_by_period)

    def compute_divide(self, column_name, period = None, requested_formulas_by_period = None):
        return self.get_or_new_holder(column_name).compute_divide(period = period,
            requested_formulas_by_period = requested_formulas_by_period)

    def get_array(self, column_name, period = None):
        return self.get_or_new_holder(column_name).get_array(period)

    def get_or_new_holder(self, column_name):
        holder = self.holder_by_name.get(column_name)
        if holder is None:
            column = self.column_by_name[column_name]
            self.holder_by_name[column_name] = holder = holders.Holder(column = column, entity = self)
            if column.formula_class is not None:
                holder.formula = column.formula_class(holder = holder)
        return holder

    def graph(self, column_name, edges, get_input_variables_and_parameters, nodes, visited):
        self.get_or_new_holder(column_name).graph(edges, get_input_variables_and_parameters, nodes, visited)

    def iter_member_persons_role_and_id(self, member):
        assert not self.is_persons_entity
        raise NotImplementedError('Method "iter_member_persons_role_and_id" is not implemented for class {}'.format(
            self.__class__.__name__))
