# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
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


class AbstractEntity(object):
    column_by_name = None  # Class attribute. Must be overridden by subclasses.
    count = None
    holder_by_name = None
    key_plural = None
    key_singular = None
    is_persons_entity = False
    roles_count = None  # Not used for individus
    step_size = None
    simulation = None
    symbol = None  # Class attribute. Must be overridden by subclasses.

    def __init__(self, simulation = None):
        self.holder_by_name = {}
        if simulation is not None:
            self.simulation = simulation

    def compute(self, column_name, requested_columns_name = None):
        return self.get_or_new_holder(column_name).compute(requested_columns_name = requested_columns_name)

    def copy_for_simulation(self, simulation):
        new = self.__class__(simulation = simulation)
        new.column_by_name = self.column_by_name
        new.count = self.count
        new.holder_by_name.update(
            (name, holder.copy_for_entity(new))
            for name, holder in self.holder_by_name.iteritems()
            )
        return new

    def get_or_new_holder(self, column_name):
        holder = self.holder_by_name.get(column_name)
        if holder is None:
            holder = self.new_holder(column_name)
        return holder

    def new_holder(self, column_name):
        column = self.column_by_name[column_name]
        self.holder_by_name[column_name] = holder = holders.Holder(column = column, entity = self)
        return holder
