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


from __future__ import division

import numpy as np

from . import periods
from .tools import empty_clone


class DatedHolder(object):
    """A view of an holder, for a given period"""
    holder = None
    period = None

    def __init__(self, holder, period):
        self.holder = holder
        self.period = period

    @property
    def array(self):
        return self.holder.get_array(self.period)

    @array.deleter
    def array(self):
        self.holder.delete_array(self.period)

    @array.setter
    def array(self, array):
        self.holder.set_array(self.period, array)

    @property
    def column(self):
        return self.holder.column

    @property
    def entity(self):
        return self.holder.entity

    def to_value_json(self, use_label = False):
        transform_dated_value_to_json = self.holder.column.transform_dated_value_to_json
        return [
            transform_dated_value_to_json(cell, use_label = use_label)
            for cell in self.array.tolist()
            ]


class Holder(object):
    _array = None  # Only used when column.is_permanent
    _array_by_period = None  # Only used when not column.is_permanent
    column = None
    entity = None
    formula = None
    formula_output_period_by_requested_period = None

    def __init__(self, column = None, entity = None):
        assert column is not None
        assert self.column is None
        self.column = column
        assert entity is not None
        self.entity = entity

    @property
    def array(self):
        if not self.column.is_permanent:
            return self.get_array(self.entity.simulation.period)
        return self._array

    @array.setter
    def array(self, array):
        simulation = self.entity.simulation
        if not self.column.is_permanent:
            return self.set_array(simulation.period, array)
        if simulation.debug or simulation.trace:
            variable_infos = (self.column.name, None)
            step = simulation.traceback.get(variable_infos)
            if step is None:
                simulation.traceback[variable_infos] = dict(
                    holder = self,
                    )
        self._array = array

    def at_period(self, period):
        return self if self.column.is_permanent else DatedHolder(self, period)

    def calculate(self, period = None, accept_other_period = False, requested_formulas_by_period = None):
        dated_holder = self.compute(period = period, accept_other_period = accept_other_period,
            requested_formulas_by_period = requested_formulas_by_period)
        return dated_holder.array

    def calculate_output(self, period):
        return self.formula.calculate_output(period)

    def clone(self, entity):
        """Copy the holder just enough to be able to run a new simulation without modifying the original simulation."""
        new = empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.iteritems():
            if key in ('_array_by_period',):
                if value is not None:
                    # There is no need to copy the arrays, because the formulas don't modify them.
                    new_dict[key] = value.copy()
            elif key not in ('entity', 'formula'):
                new_dict[key] = value

        new_dict['entity'] = entity
        # Caution: formula must be cloned after the entity has been set into new.
        formula = self.formula
        if formula is not None:
            new_dict['formula'] = formula.clone(new)

        return new

    def compute(self, period = None, accept_other_period = False, requested_formulas_by_period = None):
        """Compute array if needed and/or convert it to requested period and return a dated holder containig it.

        The returned dated holder is always of the requested period and this method never returns None.
        """
        entity = self.entity
        simulation = entity.simulation
        if period is None:
            period = simulation.period
        column = self.column

        # First look for dated_holders covering the whole period (without hole).
        dated_holder = self.at_period(period)
        if dated_holder.array is not None:
            return dated_holder
        assert self._array is None  # self._array should always be None when dated_holder.array is None.

        column_start_instant = periods.instant(column.start)
        column_stop_instant = periods.instant(column.end)
        if (column_start_instant is None or column_start_instant <= period.start) \
                and (column_stop_instant is None or period.start <= column_stop_instant):
            formula_dated_holder = self.formula.compute(period = period,
                requested_formulas_by_period = requested_formulas_by_period)
            assert formula_dated_holder is not None
            if not column.is_permanent:
                assert accept_other_period or formula_dated_holder.period == period, \
                    u"Requested period {} differs from {} returned by variable {}".format(period,
                        formula_dated_holder.period, column.name)
            return formula_dated_holder
        array = np.empty(entity.count, dtype = column.dtype)
        array.fill(column.default)
        dated_holder.array = array
        return dated_holder

    def compute_add(self, period = None, requested_formulas_by_period = None):
        dated_holder = self.at_period(period)
        if dated_holder.array is not None:
            return dated_holder

        array = None
        unit = period.unit
        if unit == u'month':
            remaining_period_months = period.size
        else:
            assert unit == u'year', unit
            remaining_period_months = period.size * 12
        requested_period = period.start.period(unit)
        while True:
            dated_holder = self.compute(accept_other_period = True, period = requested_period,
                requested_formulas_by_period = requested_formulas_by_period)
            requested_start = requested_period.start
            returned_period = dated_holder.period
            returned_start = returned_period.start
            assert returned_start.day == 1
            # Note: A dated formula may start after requested period => returned_start is not always equal to
            # requested_start.
            assert returned_start >= requested_start, \
                "Period {} returned by variable {} doesn't have the same start as requested period {}.".format(
                    returned_period, self.column.name, requested_period)
            if returned_period.unit == u'month':
                returned_period_months = returned_period.size
            else:
                assert returned_period.unit == u'year', \
                    "Requested a monthly or yearly period. Got {} returned by variable {}.".format(
                        returned_period, self.column.name)
                returned_period_months = returned_period.size * 12
            requested_start_months = requested_start.year * 12 + requested_start.month
            returned_start_months = returned_start.year * 12 + returned_start.month
            returned_period_months = returned_start_months + returned_period_months - requested_start_months
            remaining_period_months -= returned_period_months
            assert remaining_period_months >= 0, \
                "Period {} returned by variable {} is larger than the requested_period {}.".format(
                    returned_period, self.column.name, requested_period)
            if array is None:
                array = dated_holder.array.copy()
            else:
                array += dated_holder.array

            if remaining_period_months <= 0:
                dated_holder = self.at_period(period)
                dated_holder.array = array
                return dated_holder
            if remaining_period_months % 12 == 0:
                requested_period = requested_start.offset(returned_period_months, u'month').period(u'year')
            else:
                requested_period = requested_start.offset(returned_period_months, u'month').period(u'month')

    def compute_add_divide(self, period = None, requested_formulas_by_period = None):
        dated_holder = self.at_period(period)
        if dated_holder.array is not None:
            return dated_holder

        array = None
        unit = period.unit
        if unit == u'month':
            remaining_period_months = period.size
        else:
            assert unit == u'year', unit
            remaining_period_months = period.size * 12
        requested_period = period.start.period(unit)
        while True:
            dated_holder = self.compute(accept_other_period = True, period = requested_period,
                requested_formulas_by_period = requested_formulas_by_period)
            requested_start = requested_period.start
            returned_period = dated_holder.period
            returned_start = returned_period.start
            assert returned_start.day == 1
            # Note: A dated formula may start after requested period.
            # assert returned_start <= requested_start <= returned_period.stop, \
            #     "Period {} returned by variable {} doesn't include start of requested period {}.".format(
            #         returned_period, self.column.name, requested_period)
            requested_start_months = requested_start.year * 12 + requested_start.month
            returned_start_months = returned_start.year * 12 + returned_start.month
            if returned_period.unit == u'month':
                intersection_months = min(requested_start_months + requested_period.size,
                    returned_start_months + returned_period.size) - requested_start_months
                intersection_array = dated_holder.array * intersection_months / returned_period.size
            else:
                assert returned_period.unit == u'year', \
                    "Requested a monthly or yearly period. Got {} returned by variable {}.".format(
                        returned_period, self.column.name)
                intersection_months = min(requested_start_months + requested_period.size,
                    returned_start_months + returned_period.size * 12) - requested_start_months
                intersection_array = dated_holder.array * intersection_months / (returned_period.size * 12)
            if array is None:
                array = intersection_array.copy()
            else:
                array += intersection_array

            remaining_period_months -= intersection_months
            if remaining_period_months <= 0:
                dated_holder = self.at_period(period)
                dated_holder.array = array
                return dated_holder
            if remaining_period_months % 12 == 0:
                requested_period = requested_start.offset(intersection_months, u'month').period(u'year')
            else:
                requested_period = requested_start.offset(intersection_months, u'month').period(u'month')

    def compute_divide(self, period = None, requested_formulas_by_period = None):
        dated_holder = self.at_period(period)
        if dated_holder.array is not None:
            return dated_holder

        array = None
        unit = period[0]
        year, month, day = period.start
        if unit == u'month':
            dated_holder = self.compute(accept_other_period = True, period = period,
                requested_formulas_by_period = requested_formulas_by_period)
            assert dated_holder.period.start <= period.start and period.stop <= dated_holder.period.stop, \
                "Period {} returned by variable {} doesn't include requested period {}.".format(
                    dated_holder.period, self.column.name, period)
            if dated_holder.period.unit == u'month':
                array = dated_holder.array * period.size / dated_holder.period.size
            else:
                assert dated_holder.period.unit == u'year', \
                    "Requested a monthly or yearly period. Got {} returned by variable {}.".format(
                        dated_holder.period, self.column.name)
                array = dated_holder.array * period.size / (12 * dated_holder.period.size)
            dated_holder = self.at_period(period)
            dated_holder.array = array
            return dated_holder
        else:
            assert unit == u'year', unit
            return self.compute(period = period, requested_formulas_by_period = requested_formulas_by_period)

    def delete_arrays(self):
        if self._array is not None:
            del self._array
        if self._array_by_period is not None:
            del self._array_by_period

    def get_array(self, period):
        if self.column.is_permanent:
            return self.array
        assert period is not None
        array_by_period = self._array_by_period
        if array_by_period is not None:
            array = array_by_period.get(period)
            if array is not None:
                return array
        return None

    def graph(self, edges, get_input_variables_and_parameters, nodes, visited):
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
        period = self.entity.simulation.period
        formula = self.formula
        if formula is None or column.start is not None and column.start > period.stop.date or column.end is not None \
                and column.end < period.start.date:
            return
        formula.graph_parameters(edges, get_input_variables_and_parameters, nodes, visited)

    def new_test_case_array(self, period):
        array = self.get_array(period)
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

    def set_array(self, period, array):
        if self.column.is_permanent:
            self.array = array
            return
        assert period is not None
        simulation = self.entity.simulation
        if simulation.debug or simulation.trace:
            variable_infos = (self.column.name, period)
            step = simulation.traceback.get(variable_infos)
            if step is None:
                simulation.traceback[variable_infos] = dict(
                    holder = self,
                    )
        array_by_period = self._array_by_period
        if array_by_period is None:
            self._array_by_period = array_by_period = {}
        array_by_period[period] = array

    def set_input(self, period, array):
        self.formula.set_input(period, array)

    def to_value_json(self, use_label = False):
        column = self.column
        transform_dated_value_to_json = column.transform_dated_value_to_json
        if column.is_permanent:
            array = self._array
            if array is None:
                return None
            return [
                transform_dated_value_to_json(cell, use_label = use_label)
                for cell in array.tolist()
                ]
        value_json = {}
        if self._array_by_period is not None:
            for period, array in self._array_by_period.iteritems():
                value_json[str(period)] = [
                    transform_dated_value_to_json(cell, use_label = use_label)
                    for cell in array.tolist()
                    ]
        return value_json
