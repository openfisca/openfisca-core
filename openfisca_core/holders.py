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


from __future__ import division

import collections
import itertools

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
        # Note: This property may return an extrapolated array.
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

    @property
    def extrapolated_array(self):
        raise NotImplementedError("Getter of property DatedHolder.extrapolated_array doesn't exist")

    @extrapolated_array.deleter
    def extrapolated_array(self):
        self.holder.delete_extrapolated_array(self.period)

    @extrapolated_array.setter
    def extrapolated_array(self, array):
        self.holder.set_extrapolated_array(self.period, array)

    def to_value_json(self):
        transform_dated_value_to_json = self.holder.column.transform_dated_value_to_json
        return [
            transform_dated_value_to_json(cell)
            for cell in self.array.tolist()
            ]


class Holder(object):
    _array = None  # Only used when column.is_permanent
    _array_by_period = None  # Only used when not column.is_permanent
    _extrapolated_array = None  # Only used when not column.is_permanent
    _extrapolated_array_by_period = None  # Only used when not column.is_permanent
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
        if not self.column.is_permanent:
            return self.get_array(self.entity.simulation.period)
        array = self._array
        if array is None:
            array = self._extrapolated_array
        return array

    @array.deleter
    def array(self):
        simulation = self.entity.simulation
        if not self.column.is_permanent:
            return self.delete_array(simulation.period)
        if simulation.trace:
            simulation.traceback.pop((self.column.name, None), None)
        del self._array

    @array.setter
    def array(self, array):
        simulation = self.entity.simulation
        if not self.column.is_permanent:
            return self.set_array(simulation.period, array)
        if simulation.trace:
            name = self.column.name
            step = simulation.traceback.get((name, None))
            if step is None:
                simulation.traceback[(name, None)] = dict(
                    holder = self,
                    )
        self._array = array

    def at_period(self, period):
        return self if self.column.is_permanent else DatedHolder(self, period)

    def calculate(self, lazy = False, period = None, requested_formulas_by_period = None):
        dated_holder = self.compute(lazy = lazy, period = period,
            requested_formulas_by_period = requested_formulas_by_period)
        return dated_holder.array

    def clone(self, entity):
        """Copy the holder just enough to be able to run a new simulation without modifying the original simulation."""
        new = empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.iteritems():
            if key in ('_array_by_period', '_extrapolated_array_by_period'):
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

    def compute(self, lazy = False, period = None, requested_formulas_by_period = None):
        """Compute array if needed and/or convert it to requested period and return a dated holder containig it.

        The returned dated holder is always of the requested period and this method never returns None.
        """
        simulation = self.entity.simulation
        if period is None:
            period = simulation.period
        start_instant = period[1]
        stop_instant = period.stop
        column = self.column
        trace = simulation.trace

        # First look for dated_holders covering the whole period (without hole).
        dated_holder = self.at_period(period)
        if dated_holder.array is not None:
            return dated_holder
        assert self._array is None  # self._array should always be None when dated_holder.array is None.

        entity = self.entity
        formula = self.formula
        if formula is not None:
            formula_period = period
            formula_start_instant = formula_period[1]
            column_start_instant = periods.instant(column.start)
            column_stop_instant = periods.instant(column.end)
            while True:
                intersection_period = formula_period.intersection(column_start_instant, column_stop_instant)
                if intersection_period is None:
                    array = np.empty(entity.count, dtype = column.dtype)
                    array.fill(column.default)
                    dated_holder.array = array
                    break
                formula_dated_holder = formula.compute(lazy = lazy, period = intersection_period,
                    requested_formulas_by_period = requested_formulas_by_period)
                assert formula_dated_holder is not None
                formula_period = formula_dated_holder.period
                formula_period = formula_period.offset(formula_period.size)
                formula_start_instant = formula_period[1]
                if formula_start_instant > stop_instant:
                    break

        if dated_holder.array is not None:
            return dated_holder
        assert self._array is None  # self._array should always be None when dated_holder.array is None.

        if trace:
            used_periods = []

        array = None
        array_by_period = self._array_by_period
        if array_by_period is not None:
            best_first_index = None
            best_fist_start_instant = None
            sorted_period_and_array_couples = sorted(array_by_period.iteritems(),
                key = lambda (period, array): period[1])
            for index, (exact_period, exact_array) in enumerate(sorted_period_and_array_couples):
                if exact_array is None:
                    continue
                exact_start_instant = exact_period.start
                if exact_start_instant == best_fist_start_instant:
                    # When encountering several periods starting with the same instant, use the smallest one.
                    continue
                if exact_start_instant <= start_instant:
                    best_first_index = index
                    best_fist_start_instant = exact_start_instant
                    if exact_start_instant == start_instant:
                        break
                else:
                    break
            if best_first_index is not None:
                remaining_start_instant = start_instant
                for exact_period, exact_array in itertools.islice(sorted_period_and_array_couples, best_first_index,
                        None):
                    if exact_array is None:
                        continue
                    exact_start_instant = exact_period.start
                    if exact_start_instant > stop_instant:
                        # The existing data arrays don't fully cover the requested period.
                        break
                    exact_stop_instant = exact_period.stop
                    if exact_start_instant <= remaining_start_instant and exact_stop_instant >= remaining_start_instant:
                        intersection_period = exact_period.intersection(remaining_start_instant, stop_instant)
                        assert intersection_period is not None
                        if column.is_period_size_independent:
                            # Use always the first value for the period, because the output period may end before
                            # the requested period (because of base instant).
                            if array is None:
                                array = np.copy(exact_array)
                        else:
                            exact_unit = exact_period[0]
                            intersection_unit = intersection_period[0]
                            if intersection_unit == exact_unit:
                                intersection_array = exact_array * intersection_period[2] / exact_period[2]
                            elif intersection_unit == u'month' and exact_unit == u'year':
                                intersection_array = exact_array * intersection_period[2] / (exact_period[2] * 12)
                            elif intersection_unit == u'year' and exact_unit == u'month':
                                intersection_array = exact_array * intersection_period[2] * 12 / exact_period[2]
                            else:
                                intersection_array = exact_array * (intersection_period.days / exact_period.days)
                            if array is None:
                                array = np.copy(intersection_array)
                            else:
                                array += intersection_array
                            if trace:
                                used_periods.append(exact_period)
                        remaining_start_instant = exact_stop_instant.offset(1, 'day')
                        if remaining_start_instant > stop_instant:
                            dated_holder.extrapolated_array = array
                            if trace:
                                simulation.traceback[(column.name, dated_holder.period)]['used_periods'] = used_periods
                            return dated_holder
                    if exact_stop_instant >= stop_instant:
                        # The existing data arrays don't fully cover the requested period.
                        break

        if not lazy and array is None:
            array = np.empty(entity.count, dtype = column.dtype)
            array.fill(column.default)
        if array is not None:
            dated_holder.extrapolated_array = array
            if trace and used_periods:
                simulation.traceback[(column.name, dated_holder.period)]['used_periods'] = used_periods
        return dated_holder

    def delete_array(self, period):
        if self.column.is_permanent:
            del self.array
            return
        assert period is not None
        simulation = self.entity.simulation
        if simulation.trace:
            simulation.traceback.pop((self.column.name, period), None)
        array_by_period = self._array_by_period
        if array_by_period is not None:
            array_by_period.pop(period, None)
            if not array_by_period:
                del self._array_by_period

    def delete_arrays(self):
        if self._array is not None:
            del self._array
        if self._array_by_period is not None:
            del self._array_by_period
        if self._extrapolated_array_by_period is not None:
            del self._extrapolated_array_by_period

    def delete_extrapolated_array(self, period):
        assert not self.column.is_permanent
        assert period is not None
        simulation = self.entity.simulation
        if simulation.trace:
            simulation.traceback.pop((self.column.name, period), None)
        extrapolated_array_by_period = self._extrapolated_array_by_period
        if extrapolated_array_by_period is not None:
            extrapolated_array_by_period.pop(period, None)
            if not extrapolated_array_by_period:
                del self._extrapolated_array_by_period

    @property
    def extrapolated_array(self):
        raise NotImplementedError("Getter of property Holder.extrapolated_array doesn't exist")

    @extrapolated_array.deleter
    def extrapolated_array(self):
        simulation = self.entity.simulation
        if not self.column.is_permanent:
            return self.delete_extrapolated_array(simulation.period)
        if simulation.trace:
            simulation.traceback.pop((self.column.name, None), None)
        del self._extrapolated_array

    @extrapolated_array.setter
    def extrapolated_array(self, extrapolated_array):
        simulation = self.entity.simulation
        if not self.column.is_permanent:
            return self.set_extrapolated_array(simulation.period, extrapolated_array)
        if simulation.trace:
            name = self.column.name
            step = simulation.traceback.get((name, None))
            if step is None:
                simulation.traceback[(name, None)] = dict(
                    holder = self,
                    )
        self._extrapolated_array = extrapolated_array

    def get_array(self, period, exact = False):
        if self.column.is_permanent:
            return self.array
        assert period is not None
        array_by_period = self._array_by_period
        if array_by_period is not None:
            array = array_by_period.get(period)
            if array is not None:
                return array
        if not exact:
            extrapolated_array_by_period = self._extrapolated_array_by_period
            if extrapolated_array_by_period is not None:
                array = extrapolated_array_by_period.get(period)
                if array is not None:
                    return array
        return None

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
        period = self.entity.simulation.period
        formula = self.formula
        if formula is None or column.start is not None and column.start > period.stop.date or column.end is not None \
                and column.end < period.start.date:
            return
        formula.graph_parameters(edges, nodes, visited)

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
        if simulation.trace:
            name = self.column.name
            step = simulation.traceback.get((name, period))
            if step is None:
                simulation.traceback[(name, period)] = dict(
                    holder = self,
                    )
        array_by_period = self._array_by_period
        if array_by_period is None:
            self._array_by_period = array_by_period = {}
        array_by_period[period] = array

    def set_extrapolated_array(self, period, array):
        assert not self.column.is_permanent
        assert period is not None
        simulation = self.entity.simulation
        if simulation.trace:
            name = self.column.name
            step = simulation.traceback.get((name, period))
            if step is None:
                simulation.traceback[(name, period)] = dict(
                    holder = self,
                    )
        extrapolated_array_by_period = self._extrapolated_array_by_period
        if extrapolated_array_by_period is None:
            self._extrapolated_array_by_period = extrapolated_array_by_period = {}
        extrapolated_array_by_period[period] = array

    def to_field_json(self, with_value = False):
        self_json = self.column.to_json()
        self_json['entity'] = self.entity.key_plural  # Override entity symbol given by column. TODO: Remove.
        formula = self.formula
        if formula is not None:
            self_json['formula'] = formula.to_json()
        simulation = self.entity.simulation
        consumers_by_variable_name = simulation.tax_benefit_system.consumers_by_variable_name
        if consumers_by_variable_name is not None:
            consumers = consumers_by_variable_name.get(self.column.name)
            self_json['consumers'] = consumers_json = []
            for consumer in sorted(consumers or []):
                consumer_holder = simulation.get_or_new_holder(consumer)
                consumer_column = consumer_holder.column
                consumers_json.append(collections.OrderedDict((
                    ('entity', consumer_holder.entity.key_plural),
                    ('label', consumer_column.label),
                    ('name', consumer_column.name),
                    )))
        if with_value:
            self_json['value'] = self.to_value_json()
        return self_json

    def to_value_json(self):
        column = self.column
        transform_dated_value_to_json = column.transform_dated_value_to_json
        if column.is_permanent:
            array = self._array
            if array is None:
                array = self._extrapolated_array
                if array is None:
                    return None
            return [
                transform_dated_value_to_json(cell)
                for cell in array.tolist()
                ]
        value_json = {}
        if self._array_by_period is not None:
            for period, array in self._array_by_period.iteritems():
                value_json[str(period)] = [
                    transform_dated_value_to_json(cell)
                    for cell in array.tolist()
                    ]
        if self._extrapolated_array_by_period is not None:
            for period, array in self._extrapolated_array_by_period.iteritems():
                value_json[str(period)] = [
                    transform_dated_value_to_json(cell)
                    for cell in array.tolist()
                    ]
        return value_json
