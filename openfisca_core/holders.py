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


import collections

import numpy as np

from . import columns


class Holder(object):
    _array = None
    column = None
    entity = None
    formula = None

    def __init__(self, column = None, entity = None):
        assert column is not None
        assert self.column is None
        self.column = column
        assert entity is not None
        self.entity = entity

    @property
    def array(self):
        return self._array

    @array.deleter
    def array(self):
        simulation = self.entity.simulation
        if simulation.trace:
            simulation.traceback.pop(self.column.name, None)
        del self._array

    @array.setter
    def array(self, array):
        simulation = self.entity.simulation
        if simulation.trace:
            name = self.column.name
            step = simulation.traceback.get(name)
            if step is None:
                simulation.traceback[name] = dict(
                    holder = self,
                    )
        self._array = array

    def calculate(self, lazy = False, requested_formulas = None):
        column = self.column
        date = self.entity.simulation.date
        formula = self.formula
        if formula is None or column.start is not None and column.start > date or column.end is not None \
                and column.end < date:
            if not lazy and self.array is None:
                self.array = np.empty(self.entity.count, dtype = column.dtype)
                self.array.fill(column.default)
            return self.array
        return formula.calculate(lazy = lazy, requested_formulas = requested_formulas)

    def copy_for_entity(self, entity):
        new = self.__class__(column = self.column, entity = entity)
        new.array = self.array
        return new

    def graph(self, edges, nodes, visited):
        column = self.column
        if self in visited:
            return
        visited.add(self)
        nodes.append(dict(
            id = column.name,
            group = self.entity.key_plural,
            label = column.name,
            title = column.label,
            ))
        date = self.entity.simulation.date
        formula = self.formula
        if formula is None or column.start is not None and column.start > date or column.end is not None \
                and column.end < date:
            return
        formula.graph_parameters(edges, nodes, visited)

    def new_test_case_array(self):
        array = self.array
        if array is None:
            return None
        entity = self.entity
        return array.reshape([entity.simulation.steps_count, entity.step_size]).sum(1)

    @property
    def real_formula(self):
        formula = self.formula
        if formula is None:
            return None
        return formula.real_formula

    def to_json(self, with_array = False):
        self_json = self.column.to_json()
        self_json['entity'] = self.entity.key_plural  # Override entity symbol given by column. TODO: Remove.
        formula = self.formula
        if formula is not None:
            self_json['formula'] = formula.to_json()
        entity = self.entity
        simulation = entity.simulation
        self_json['consumers'] = consumers_json = []
        for consumer in sorted(self.column.consumers or []):
            consumer_holder = simulation.get_or_new_holder(consumer)
            consumer_column = consumer_holder.column
            consumers_json.append(collections.OrderedDict((
                ('entity', consumer_holder.entity.key_plural),
                ('label', consumer_column.label),
                ('name', consumer_column.name),
                )))

        if with_array and self.array is not None:
            self_json['array'] = self.array.tolist()
        return self_json
