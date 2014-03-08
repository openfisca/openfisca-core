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


import numpy as np

from . import columns


class Holder(object):
    array = None
    column = None
    entity = None
    formula = None

    def __init__(self, column = None, entity = None):
        assert column is not None
        assert self.column is None
        self.column = column
        assert entity is not None
        self.entity = entity
        if isinstance(column, columns.Prestation):
            self.formula = column.formula_constructor(holder = self)

    def compute(self, requested_columns_name = None):
        column = self.column
        date = self.entity.simulation.date
        if column.start is not None and column.start > date or column.end is not None and column.end < date:
            if self.array is None:
                self.array = np.empty(self.entity.count, dtype = column._dtype)
                self.array.fill(column._default)
            return self
        formula = self.formula
        if formula is None:
            if self.array is None:
                self.array = np.empty(self.entity.count, dtype = column._dtype)
                self.array.fill(column._default)
            return self
        return formula(requested_columns_name = requested_columns_name)

    def copy_for_entity(self, entity):
        new = self.__class__(column = self.column, entity = entity)
        new.array = self.array
        return new
