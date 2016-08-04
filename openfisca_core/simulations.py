# -*- coding: utf-8 -*-


import collections

import numpy as np

from . import periods, holders
from .tools import empty_clone, stringify_array


class Simulation(object):
    compact_legislation_by_instant_cache = None
    debug = False
    debug_all = False  # When False, log only formula calls with non-default parameters.
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

    def __init__(self, debug = False, debug_all = False, period = None, tax_benefit_system = None,
    trace = False, opt_out_cache = False):
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
        self.opt_out_cache = opt_out_cache
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
        print_trace = parameters.pop('print_trace', False)
        if print_trace:
            print_trace_kwargs = {}
            max_depth = parameters.pop('max_depth', None)
            if max_depth is not None:
                print_trace_kwargs['max_depth'] = max_depth
            show_default_values = parameters.pop('show_default_values', None)
            if show_default_values is not None:
                print_trace_kwargs['show_default_values'] = show_default_values
        if (self.debug or self.trace) and self.stack_trace:
            variable_infos = (column_name, period)
            calling_frame = self.stack_trace[-1]
            caller_input_variables_infos = calling_frame['input_variables_infos']
            if variable_infos not in caller_input_variables_infos:
                caller_input_variables_infos.append(variable_infos)
        holder = self.get_or_new_holder(column_name)
        result = holder.compute(period = period, **parameters)
        if print_trace:
            self.print_trace(variable_name=column_name, period=period, **print_trace_kwargs)
        return result

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
        if holder is None:
            column = self.tax_benefit_system.get_column(column_name, check_existence = True)
            entity = self.get_variable_entity(column_name)
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

    def find_traceback_step(self, variable_name, period):
        assert isinstance(period, periods.Period), period
        column = self.tax_benefit_system.get_column(variable_name, check_existence=True)
        step = self.traceback.get((variable_name, period))
        if step is None and column.is_period_size_independent:
            period = None
        step = self.traceback.get((variable_name, period))
        return step

    def print_trace(self, variable_name, period, max_depth=3, show_default_values=True):
        """
        Print the dependencies of all the variables computed since the creation of the simulation.

        The `max_depth` parameter tells how much levels of the printed tree to show. Use -1 to disable limit.

        The simulation must have been initialized with `trace=True` argument.
        """
        def traverse(current_variable_name, current_period, depth):
            step = self.find_traceback_step(current_variable_name, current_period)
            assert step is not None
            holder = self.get_holder(current_variable_name)
            has_default_value = np.all(holder.get_array(current_period) == holder.column.default)
            if depth == 0 or (show_default_values or not has_default_value):
                indent = u'|     ' * (depth - 1) + u'|---> ' \
                    if depth > 0 \
                    else ''
                print(indent + self.stringify_variable_for_period_with_array(current_variable_name, current_period))
            input_variables_infos = step.get('input_variables_infos')
            if (max_depth == -1 or depth < max_depth) and input_variables_infos is not None:
                    for index, (child_variable_name, child_period) in enumerate(input_variables_infos):
                        traverse(child_variable_name, child_period, depth + 1)
        if not isinstance(max_depth, int) or max_depth < -1:
            raise ValueError(u'`max_depth` argument must be >= -1')
        if not self.trace:
            raise ValueError(u'This simulation has not been initialized with `trace=True` so the computation '
                'did not collect any trace information.')
        assert self.traceback is not None
        if not isinstance(period, periods.Period):
            period = periods.period(period)
        step = self.find_traceback_step(variable_name, period)
        if step is None:
            raise ValueError(u'The given `variable_name` "{0}" was not calculated for the given `period` "{1}". '
                u'It is therefore not possible to display the trace. '
                u'You should do `simulation.calculate({0!r}, {1}, print_trace=True)`.'.format(
                    variable_name, period))
        traverse(variable_name, period, depth=0)

    def stringify_variable_for_period_with_array(self, variable_name, period):
        holder = self.get_holder(variable_name)
        return u'{}@{}<{}>{}'.format(
            variable_name,
            holder.entity.key_plural,
            str(period),
            stringify_array(holder.get_array(period)),
            )

    def stringify_input_variables_infos(self, input_variables_infos):
        return u', '.join(
            self.stringify_variable_for_period_with_array(
                variable_name=input_variable_name,
                period=input_variable_period,
                )
            for input_variable_name, input_variable_period in input_variables_infos
            )

    # Fixme: to rewrite
    def to_input_variables_json(self):
        return None

    def get_variable_entity(self, variable_name):
        column = self.tax_benefit_system.get_column(variable_name, check_existence = True)
        return self.entity_by_key_plural[column.entity_key_plural]
