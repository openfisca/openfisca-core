# -*- coding: utf-8 -*-


import collections

from . import periods, holders
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
        self.holder_by_name = {}

        # To keep track of the values (formulas and periods) being calculated to detect circular definitions.
        # See use in formulas.py.
        # The data structure of requested_periods_by_variable_name is: {variable_name: [period1, period2]}
        self.requested_periods_by_variable_name = {}
        self.max_nb_cycles = None

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

    def calculate(self, column_name, period = None, **parameters):
        if period is None:
            period = self.period
        return self.compute(column_name, period = period, **parameters).array

    def calculate_add(self, column_name, period = None, **parameters):
        if period is None:
            period = self.period
        return self.compute_add(column_name, period = period, **parameters).array

    def calculate_add_divide(self, column_name, period = None, **parameters):
        if period is None:
            period = self.period
        return self.compute_add_divide(column_name, period = period, **parameters).array

    def calculate_divide(self, column_name, period = None, **parameters):
        if period is None:
            period = self.period
        return self.compute_divide(column_name, period = period, **parameters).array

    def calculate_output(self, column_name, period = None):
        """Calculate the value using calculate_output hooks in formula classes."""
        if period is None:
            period = self.period
        elif not isinstance(period, periods.Period):
            period = periods.period(period)
        holder = self.get_or_new_holder(column_name)
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
        new_dict['holder_by_name'] = {
            name: holder.clone()
            for name, holder in self.holder_by_name.iteritems()
            }
        for entity in entity_by_key_plural.itervalues():
            if entity.is_persons_entity:
                new_dict['persons'] = entity
                break

        return new

    def compute(self, column_name, period = None, **parameters):
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
        holder = self.get_or_new_holder(column_name)
        return holder.compute(period = period, **parameters)

    def compute_add(self, column_name, period = None, **parameters):
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
        holder = self.get_or_new_holder(column_name)
        return holder.compute_add(period = period, **parameters)

    def compute_add_divide(self, column_name, period = None, **parameters):
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
        holder = self.get_or_new_holder(column_name)
        return holder.compute_add_divide(period = period, **parameters)

    def compute_divide(self, column_name, period = None, **parameters):
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
        holder = self.get_or_new_holder(column_name)
        return holder.compute_divide(period = period, **parameters)

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
        return self.get_or_new_holder(column_name).get_array(period)

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
        if default is UnboundLocalError:
            return self.holder_by_name[column_name]
        return self.holder_by_name.get(column_name, default)

    def get_or_new_holder(self, column_name):
        holder = self.holder_by_name.get(column_name)
        entity = self.entity_by_column_name[column_name]
        if holder is None:
            column = entity.column_by_name[column_name]
            self.holder_by_name[column_name] = holder = holders.Holder(column = column, entity = entity)
            if column.formula_class is not None:
                holder.formula = column.formula_class(holder = holder)
        return holder

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
        self.get_or_new_holder(column_name).graph(edges, get_input_variables_and_parameters, nodes, visited)

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
