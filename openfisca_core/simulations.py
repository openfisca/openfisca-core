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


import collections

from . import periods
from .tools import empty_clone, stringify_array


class Simulation(object):
    compact_legislation_by_instant_cache = None
    debug = False
    debug_all = False  # When False, log only formula calls with non-default parameters.
    entity_by_column_name = None
    entity_by_key_plural = None
    entity_by_key_singular = None
    period = None
    persons = None
    reference_compact_legislation_by_instant_cache = None
    stack_trace = None
    steps_count = 1
    tax_benefit_system = None
    trace = False
    traceback = None

    def __init__(self, debug = False, debug_all = False, period = None, tax_benefit_system = None, trace = False):
        assert isinstance(period, periods.Period)
        self.period = period
        if debug:
            self.debug = True
        if debug_all:
            assert debug
            self.debug_all = True
        assert tax_benefit_system is not None
        self.tax_benefit_system = tax_benefit_system
        if trace:
            self.trace = True
        if debug or trace:
            self.stack_trace = collections.deque()
            self.traceback = collections.OrderedDict()

        # Note: Since simulations are short-lived and must be fast, don't use weakrefs for cache.
        self.compact_legislation_by_instant_cache = {}
        self.reference_compact_legislation_by_instant_cache = {}

        entity_class_by_key_plural = tax_benefit_system.entity_class_by_key_plural
        self.entity_by_key_plural = entity_by_key_plural = dict(
            (key_plural, entity_class(simulation = self))
            for key_plural, entity_class in entity_class_by_key_plural.iteritems()
            )
        self.entity_by_column_name = dict(
            (column_name, entity)
            for entity in entity_by_key_plural.itervalues()
            for column_name in entity.column_by_name.iterkeys()
            )
        self.entity_by_key_singular = dict(
            (entity.key_singular, entity)
            for entity in entity_by_key_plural.itervalues()
            )
        for entity in entity_by_key_plural.itervalues():
            if entity.is_persons_entity:
                self.persons = entity
                break

    def calculate(self, column_name, period = None, accept_other_period = False, requested_formulas_by_period = None):
        if period is None:
            period = self.period
        return self.compute(column_name, period = period, accept_other_period = accept_other_period,
            requested_formulas_by_period = requested_formulas_by_period).array

    def calculate_add(self, column_name, period = None, requested_formulas_by_period = None):
        if period is None:
            period = self.period
        return self.compute_add(column_name, period = period,
            requested_formulas_by_period = requested_formulas_by_period).array

    def calculate_add_divide(self, column_name, period = None, requested_formulas_by_period = None):
        if period is None:
            period = self.period
        return self.compute_add_divide(column_name, period = period,
            requested_formulas_by_period = requested_formulas_by_period).array

    def calculate_divide(self, column_name, period = None, requested_formulas_by_period = None):
        if period is None:
            period = self.period
        return self.compute_divide(column_name, period = period,
            requested_formulas_by_period = requested_formulas_by_period).array

    def calculate_output(self, column_name, period = None):
        """Calculate the value using calculate_output hooks in formula classes."""
        if period is None:
            period = self.period
        elif not isinstance(period, periods.Period):
            period = periods.period(period)
        entity = self.entity_by_column_name[column_name]
        holder = entity.get_or_new_holder(column_name)
        return holder.calculate_output(period)

    def clone(self, debug = False, debug_all = False, trace = False):
        """Copy the simulation just enough to be able to run the copy without modifying the original simulation."""
        new = empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.iteritems():
            if key not in ('debug', 'debug_all', 'entity_by_key_plural', 'persons', 'trace'):
                new_dict[key] = value

        if debug:
            new_dict['debug'] = True
        if debug_all:
            new_dict['debug_all'] = True
        if trace:
            new_dict['trace'] = True
        if debug or trace:
            new_dict['stack_trace'] = collections.deque()
            new_dict['traceback'] = collections.OrderedDict()

        new_dict['entity_by_key_plural'] = entity_by_key_plural = dict(
            (key_plural, entity.clone(simulation = new))
            for key_plural, entity in self.entity_by_key_plural.iteritems()
            )
        new_dict['entity_by_column_name'] = dict(
            (column_name, entity)
            for entity in entity_by_key_plural.itervalues()
            for column_name in entity.column_by_name.iterkeys()
            )
        new_dict['entity_by_key_singular'] = dict(
            (entity.key_singular, entity)
            for entity in entity_by_key_plural.itervalues()
            )
        for entity in entity_by_key_plural.itervalues():
            if entity.is_persons_entity:
                new_dict['persons'] = entity
                break

        return new

    def compute(self, column_name, period = None, accept_other_period = False, requested_formulas_by_period = None):
        if period is None:
            period = self.period
        elif not isinstance(period, periods.Period):
            period = periods.period(period)
        if (self.debug or self.trace) and self.stack_trace:
            variable_infos = (column_name, period)
            calling_frame = self.stack_trace[-1]
            caller_input_variables_infos = calling_frame['input_variables_infos']
            if variable_infos not in caller_input_variables_infos:
                caller_input_variables_infos.append(variable_infos)
        return self.entity_by_column_name[column_name].compute(column_name, period = period,
            accept_other_period = accept_other_period, requested_formulas_by_period = requested_formulas_by_period)

    def compute_add(self, column_name, period = None, requested_formulas_by_period = None):
        if period is None:
            period = self.period
        elif not isinstance(period, periods.Period):
            period = periods.period(period)
        if (self.debug or self.trace) and self.stack_trace:
            variable_infos = (column_name, period)
            calling_frame = self.stack_trace[-1]
            caller_input_variables_infos = calling_frame['input_variables_infos']
            if variable_infos not in caller_input_variables_infos:
                caller_input_variables_infos.append(variable_infos)
        return self.entity_by_column_name[column_name].compute_add(column_name, period = period,
            requested_formulas_by_period = requested_formulas_by_period)

    def compute_add_divide(self, column_name, period = None, requested_formulas_by_period = None):
        if period is None:
            period = self.period
        elif not isinstance(period, periods.Period):
            period = periods.period(period)
        if (self.debug or self.trace) and self.stack_trace:
            variable_infos = (column_name, period)
            calling_frame = self.stack_trace[-1]
            caller_input_variables_infos = calling_frame['input_variables_infos']
            if variable_infos not in caller_input_variables_infos:
                caller_input_variables_infos.append(variable_infos)
        return self.entity_by_column_name[column_name].compute_add_divide(column_name, period = period,
            requested_formulas_by_period = requested_formulas_by_period)

    def compute_divide(self, column_name, period = None, requested_formulas_by_period = None):
        if period is None:
            period = self.period
        elif not isinstance(period, periods.Period):
            period = periods.period(period)
        if (self.debug or self.trace) and self.stack_trace:
            variable_infos = (column_name, period)
            calling_frame = self.stack_trace[-1]
            caller_input_variables_infos = calling_frame['input_variables_infos']
            if variable_infos not in caller_input_variables_infos:
                caller_input_variables_infos.append(variable_infos)
        return self.entity_by_column_name[column_name].compute_divide(column_name, period = period,
            requested_formulas_by_period = requested_formulas_by_period)

    def get_array(self, column_name, period = None):
        if period is None:
            period = self.period
        elif not isinstance(period, periods.Period):
            period = periods.period(period)
        if (self.debug or self.trace) and self.stack_trace:
            variable_infos = (column_name, period)
            calling_frame = self.stack_trace[-1]
            caller_input_variables_infos = calling_frame['input_variables_infos']
            if variable_infos not in caller_input_variables_infos:
                caller_input_variables_infos.append(variable_infos)
        return self.entity_by_column_name[column_name].get_array(column_name, period)

    def get_compact_legislation(self, instant):
        compact_legislation = self.compact_legislation_by_instant_cache.get(instant)
        if compact_legislation is None:
            compact_legislation = self.tax_benefit_system.get_compact_legislation(
                instant = instant,
                traced_simulation = self if self.trace else None,
                )
            self.compact_legislation_by_instant_cache[instant] = compact_legislation
        return compact_legislation

    def get_holder(self, column_name, default = UnboundLocalError):
        entity = self.entity_by_column_name[column_name]
        if default is UnboundLocalError:
            return entity.holder_by_name[column_name]
        return entity.holder_by_name.get(column_name, default)

    def get_or_new_holder(self, column_name):
        entity = self.entity_by_column_name[column_name]
        return entity.get_or_new_holder(column_name)

    def get_reference_compact_legislation(self, instant):
        reference_compact_legislation = self.reference_compact_legislation_by_instant_cache.get(instant)
        if reference_compact_legislation is None:
            reference_compact_legislation = self.tax_benefit_system.get_reference_compact_legislation(
                instant = instant,
                traced_simulation = self if self.trace else None,
                )
            self.reference_compact_legislation_by_instant_cache[instant] = reference_compact_legislation
        return reference_compact_legislation

    def graph(self, column_name, edges, get_input_variables_and_parameters, nodes, visited):
        self.entity_by_column_name[column_name].graph(column_name, edges, get_input_variables_and_parameters, nodes,
            visited)

    def legislation_at(self, instant, reference = False):
        assert isinstance(instant, periods.Instant), "Expected an instant. Got: {}".format(instant)
        if reference:
            return self.get_reference_compact_legislation(instant)
        return self.get_compact_legislation(instant)

    def stringify_input_variables_infos(self, input_variables_infos):
        return u', '.join(
            u'{}@{}<{}>{}'.format(
                input_holder.column.name,
                input_holder.entity.key_plural,
                str(input_variable_period),
                stringify_array(input_holder.get_array(input_variable_period)),
                )
            for input_holder, input_variable_period in (
                (self.get_holder(input_variable_name), input_variable_period1)
                for input_variable_name, input_variable_period1 in input_variables_infos
                )
            )

    def to_input_variables_json(self):
        return {
            column_name: self.get_holder(column_name).to_value_json()
            for entity in self.entity_by_key_plural.itervalues()
            for column_name in entity.column_by_name.iterkeys()
            if column_name in entity.holder_by_name
            }
