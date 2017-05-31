# -*- coding: utf-8 -*-


import collections

from . import periods, holders
from .commons import empty_clone, stringify_array


class Simulation(object):
    compact_legislation_by_instant_cache = None
    debug = False
    debug_all = False  # When False, log only formula calls with non-default parameters.
    period = None
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

        self.instantiate_entities()

    def instantiate_entities(self):
        self.persons = self.tax_benefit_system.person_entity(self)
        setattr(self, self.persons.key, self.persons)
        self.entities = {self.persons.key: self.persons}

        for entity_definition in self.tax_benefit_system.group_entities:
            entity = entity_definition(self)
            self.entities[entity_definition.key] = entity
            setattr(self, entity.key, entity)

    def calculate(self, column_name, period, **parameters):
        return self.compute(column_name, period = period, **parameters).array

    def calculate_add(self, column_name, period, **parameters):
        return self.compute_add(column_name, period = period, **parameters).array

    def calculate_divide(self, column_name, period, **parameters):
        return self.compute_divide(column_name, period = period, **parameters).array

    def calculate_output(self, column_name, period):
        """Calculate the value using calculate_output hooks in formula classes."""
        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)
        holder = self.get_or_new_holder(column_name)
        return holder.calculate_output(period)

    def clone(self, debug = False, debug_all = False, trace = False):
        """Copy the simulation just enough to be able to run the copy without modifying the original simulation."""
        new = empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.iteritems():
            if key not in ('debug', 'debug_all', 'trace'):
                new_dict[key] = value

        for entity in new.entities.itervalues():
            entity.simulation = new

        if debug:
            new_dict['debug'] = True
        if debug_all:
            new_dict['debug_all'] = True
        if trace:
            new_dict['trace'] = True
        if debug or trace:
            new_dict['stack_trace'] = collections.deque()
            new_dict['traceback'] = collections.OrderedDict()

        new_dict['holder_by_name'] = {
            name: holder.clone()
            for name, holder in self.holder_by_name.iteritems()
            }
        return new

    def compute(self, column_name, period, **parameters):
        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)
        if (self.debug or self.trace) and self.stack_trace:
            variable_infos = (column_name, period)
            calling_frame = self.stack_trace[-1]
            caller_input_variables_infos = calling_frame['input_variables_infos']
            if variable_infos not in caller_input_variables_infos:
                caller_input_variables_infos.append(variable_infos)
        holder = self.get_or_new_holder(column_name)
        result = holder.compute(period = period, **parameters)
        return result

    def compute_add(self, column_name, period, **parameters):
        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)
        if (self.debug or self.trace) and self.stack_trace:
            variable_infos = (column_name, period)
            calling_frame = self.stack_trace[-1]
            caller_input_variables_infos = calling_frame['input_variables_infos']
            if variable_infos not in caller_input_variables_infos:
                caller_input_variables_infos.append(variable_infos)
        holder = self.get_or_new_holder(column_name)
        return holder.compute_add(period = period, **parameters)

    def compute_divide(self, column_name, period, **parameters):
        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)
        if (self.debug or self.trace) and self.stack_trace:
            variable_infos = (column_name, period)
            calling_frame = self.stack_trace[-1]
            caller_input_variables_infos = calling_frame['input_variables_infos']
            if variable_infos not in caller_input_variables_infos:
                caller_input_variables_infos.append(variable_infos)
        holder = self.get_or_new_holder(column_name)
        return holder.compute_divide(period = period, **parameters)

    def get_array(self, column_name, period):
        if period is not None and not isinstance(period, periods.Period):
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
            self.holder_by_name[column_name] = holder = holders.Holder(
                self,
                column = column,
                )
            if column.formula_class is not None:
                holder.formula = column.formula_class(holder = holder)  # Instanciates a Formula
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
        if isinstance(instant, periods.Period):
            instant = instant.start
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

    def stringify_variable_for_period_with_array(self, variable_name, period):
        holder = self.get_holder(variable_name)
        return u'{}@{}<{}>{}'.format(
            variable_name,
            holder.entity.key,
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
        return self.get_entity(column.entity)

    def get_entity(self, entity_type):
        return self.entities[entity_type.key]
