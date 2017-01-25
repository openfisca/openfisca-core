# -*- coding: utf-8 -*-


from __future__ import division

import collections
import datetime
import inspect
import itertools
import logging

import numpy as np

from . import columns, holders, legislations, periods
from .base_functions import (
    permanent_default_value,
    requested_period_default_value_neutralized,
    requested_period_default_value,
    requested_period_last_or_next_value,
    requested_period_last_value,
    )
from .commons import empty_clone, stringify_array


log = logging.getLogger(__name__)


ADD = 'add'
DIVIDE = 'divide'

# Exceptions


class NaNCreationError(Exception):
    pass


class CycleError(Exception):
    pass

# Formulas


class AbstractFormula(object):
    comments = None
    holder = None
    start_line_number = None
    source_code = None
    source_file_path = None

    def __init__(self, holder = None):
        assert holder is not None
        self.holder = holder

    def calculate_output(self, period):
        return self.holder.compute(period).array

    def clone(self, holder, keys_to_skip = None):
        """Copy the formula just enough to be able to run a new simulation without modifying the original simulation."""
        new = empty_clone(self)
        new_dict = new.__dict__

        if keys_to_skip is None:
            keys_to_skip = set()
        keys_to_skip.add('holder')
        for key, value in self.__dict__.iteritems():
            if key not in keys_to_skip:
                new_dict[key] = value

        new_dict['holder'] = holder

        return new

    def default_values(self):
        '''Return a new NumPy array which length is the entity count, filled with default values.'''
        return self.zeros() + self.holder.column.default

    @property
    def real_formula(self):
        return self

    def set_input(self, period, array):
        self.holder.put_in_cache(array, period)

    def zeros(self, **kwargs):
        '''
        Return a new NumPy array which length is the entity count, filled with zeros.

        kwargs are forwarded to np.zeros.
        '''
        return np.zeros(self.holder.entity.count, **kwargs)


class AbstractGroupedFormula(AbstractFormula):
    used_formula = None

    @property
    def real_formula(self):
        used_formula = self.used_formula
        if used_formula is None:
            return None
        return used_formula.real_formula


class DatedFormula(AbstractGroupedFormula):
    base_function = None  # Class attribute. Overridden by subclasses
    dated_formulas = None  # A list of dictionaries containing a formula jointly with start and stop instants
    dated_formulas_class = None  # Class attribute

    def __init__(self, holder = None):
        super(DatedFormula, self).__init__(holder = holder)

        self.dated_formulas = [
            dict(
                formula = dated_formula_class['formula_class'](holder = holder),
                start_instant = dated_formula_class['start_instant'],
                stop_instant = dated_formula_class['stop_instant'],
                )
            for dated_formula_class in self.dated_formulas_class
            ]
        assert self.dated_formulas

    @classmethod
    def at_instant(cls, instant, default = UnboundLocalError):
        assert isinstance(instant, periods.Instant)
        for dated_formula_class in cls.dated_formulas_class:
            start_instant = dated_formula_class['start_instant']
            stop_instant = dated_formula_class['stop_instant']
            if (start_instant is None or start_instant <= instant) and (
                    stop_instant is None or instant <= stop_instant):
                return dated_formula_class['formula_class']
        if default is UnboundLocalError:
            raise KeyError(instant)
        return default

    def clone(self, holder, keys_to_skip = None):
        """Copy the formula just enough to be able to run a new simulation without modifying the original simulation."""
        if keys_to_skip is None:
            keys_to_skip = set()
        keys_to_skip.add('dated_formulas')
        new = super(DatedFormula, self).clone(holder, keys_to_skip = keys_to_skip)

        new.dated_formulas = [
            {
                key: value.clone(holder) if key == 'formula' else value
                for key, value in dated_formula.iteritems()
                }
            for dated_formula in self.dated_formulas
            ]

        return new

    def compute(self, period = None, **parameters):
        dated_holder = None
        stop_instant = period.stop
        for dated_formula in self.dated_formulas:
            if dated_formula['start_instant'] > stop_instant:
                break
            output_period = period.intersection(dated_formula['start_instant'], dated_formula['stop_instant'])
            if output_period is None:
                continue
            dated_holder = dated_formula['formula'].compute(period = output_period, **parameters)
            if dated_holder.array is None:
                break
            self.used_formula = dated_formula['formula']
            return dated_holder

        holder = self.holder
        array = holder.default_array()
        return holder.put_in_cache(array, period, parameters.get('extra_params'))

    def graph_parameters(self, edges, get_input_variables_and_parameters, nodes, visited):
        """Recursively build a graph of formulas."""
        for dated_formula in self.dated_formulas:
            dated_formula['formula'].graph_parameters(edges, get_input_variables_and_parameters, nodes, visited)

    def to_json(self, get_input_variables_and_parameters = None, with_input_variables_details = False):
        return collections.OrderedDict((
            ('@type', u'DatedFormula'),
            ('dated_formulas', [
                dict(
                    formula = dated_formula['formula'].to_json(
                        get_input_variables_and_parameters = get_input_variables_and_parameters,
                        with_input_variables_details = with_input_variables_details,
                        ),
                    start_instant = (None if dated_formula['start_instant'] is None
                        else str(dated_formula['start_instant'])),
                    stop_instant = (None if dated_formula['stop_instant'] is None
                        else str(dated_formula['stop_instant'])),
                    )
                for dated_formula in self.dated_formulas
                ]),
            ))


class SimpleFormula(AbstractFormula):
    base_function = None  # Class attribute. Overridden by subclasses
    function = None  # Class attribute. Overridden by subclasses

    def any_by_roles(self, array_or_dated_holder, entity = None, roles = None):
        holder = self.holder
        simulation = holder.simulation
        persons = simulation.persons
        if entity is None:
            entity = holder.entity
        else:
            assert entity in simulation.tax_benefit_system.entities, u"Unknown entity: {}".format(entity).encode('utf-8')

        assert not entity.is_person
        if isinstance(array_or_dated_holder, (holders.DatedHolder, holders.Holder)):
            assert array_or_dated_holder.entity.is_person
            array = array_or_dated_holder.array
        else:
            array = array_or_dated_holder
            assert isinstance(array, np.ndarray), u"Expected a holder or a Numpy array. Got: {}".format(array).encode(
                'utf-8')
            persons_count = persons.count
            assert array.size == persons_count, u"Expected an array of size {}. Got: {}".format(persons_count,
                array.size)
        entity_index_array = simulation.get_entity(entity).members_entity_id

        if roles is None:
            roles = range(entity.roles_count)
        target_array = self.zeros(dtype = np.bool)
        for role in roles:
            # TODO Mettre les filtres en cache dans la simulation
            boolean_filter = simulation.get_entity(entity).members_legacy_role == role
            target_array[entity_index_array[boolean_filter]] += array[boolean_filter]
        return target_array

    def cast_from_entity_to_role(self, array_or_dated_holder, default = None, entity = None, role = None):
        """Cast an entity array to a persons array, setting only cells of persons having the given role."""
        assert isinstance(role, int)
        return self.cast_from_entity_to_roles(array_or_dated_holder, default = default, entity = entity, roles = [role])

    def cast_from_entity_to_roles(self, array_or_dated_holder, default = None, entity = None, roles = None):
        """Cast an entity array to a persons array, setting only cells of persons having one of the given roles.

        When no roles are given, it means "all the roles" => every cell is set.
        """
        holder = self.holder
        simulation = holder.simulation
        persons = simulation.persons
        if isinstance(array_or_dated_holder, (holders.DatedHolder, holders.Holder)):
            if entity is None:
                entity = array_or_dated_holder.entity
            else:
                assert entity in simulation.tax_benefit_system.entities, u"Unknown entity: {}".format(entity).encode('utf-8')

                assert entity == array_or_dated_holder.entity, \
                    u"""Holder entity "{}" and given entity "{}" don't match""".format(entity.key,
                        array_or_dated_holder.column.entity.key).encode('utf-8')
            array = array_or_dated_holder.array
            if default is None:
                default = array_or_dated_holder.column.default
        else:
            assert entity in simulation.tax_benefit_system.entities, u"Unknown entity: {}".format(entity).encode('utf-8')

            array = array_or_dated_holder
            assert isinstance(array, np.ndarray), u"Expected a holder or a Numpy array. Got: {}".format(array).encode(
                'utf-8')
            entity_count = entity.count
            assert array.size == entity_count, u"Expected an array of size {}. Got: {}".format(entity_count,
                array.size)
            if default is None:
                default = 0
        assert not entity.is_person
        persons_count = persons.count
        target_array = np.empty(persons_count, dtype = array.dtype)
        target_array.fill(default)
        entity_index_array = simulation.get_entity(entity).members_entity_id

        if roles is None:
            roles = range(entity.roles_count)
        for role in roles:
            boolean_filter = simulation.get_entity(entity).members_legacy_role == role
            try:
                target_array[boolean_filter] = array[entity_index_array[boolean_filter]]
            except:
                log.error(u'An error occurred while transforming array for role {}[{}] in function {}'.format(
                    entity.key, role, holder.column.name))
                raise
        return target_array

    def check_for_cycle(self, period):
        """
        Return a boolean telling if the current variable has already been called without being allowed by
        the parameter max_nb_cycles of the calculate method.
        """
        def get_error_message():
            return u'Circular definition detected on formula {}<{}>. Formulas and periods involved: {}.'.format(
                column.name,
                period,
                u', '.join(sorted(set(
                    u'{}<{}>'.format(variable_name, period2)
                    for variable_name, periods in requested_periods_by_variable_name.iteritems()
                    for period2 in periods
                    ))).encode('utf-8'),
                )
        simulation = self.holder.simulation
        requested_periods_by_variable_name = simulation.requested_periods_by_variable_name
        column = self.holder.column
        variable_name = column.name
        if variable_name in requested_periods_by_variable_name:
            # Make sure the formula doesn't call itself for the same period it is being called for.
            # It would be a pure circular definition.
            requested_periods = requested_periods_by_variable_name[variable_name]
            assert period not in requested_periods and not column.is_permanent, get_error_message()
            if simulation.max_nb_cycles is None or len(requested_periods) > simulation.max_nb_cycles:
                message = get_error_message()
                if simulation.max_nb_cycles is None:
                    message += ' Hint: use "max_nb_cycles = 0" to get a default value, or "= N" to allow N cycles.'
                raise CycleError(message)
            else:
                requested_periods.append(period)
        else:
            requested_periods_by_variable_name[variable_name] = [period]

    def clean_cycle_detection_data(self):
        """
        When the value of a formula have been computed, remove the period from
        requested_periods_by_variable_name[variable_name] and delete the latter if empty.
        """
        simulation = self.holder.simulation
        column = self.holder.column
        variable_name = column.name
        requested_periods_by_variable_name = simulation.requested_periods_by_variable_name
        if variable_name in requested_periods_by_variable_name:
            requested_periods_by_variable_name[variable_name].pop()
            if len(requested_periods_by_variable_name[variable_name]) == 0:
                del requested_periods_by_variable_name[variable_name]

    def compute(self, period = None, **parameters):
        """
        Call the formula function (if needed) and return a dated holder containing its result.

        If a cycle is detected, a CycleError is raised.
        To avoid it a formula can use the max_nb_cycles parameter (int >= 0) so when the cycle is detected,
        the exceptions mechanism rewinds up to the first variable called with max_nb_cycles != None,
        and a default value is returned for the latter variable.
        Then the calculation continues normally.
        """
        assert period is not None
        holder = self.holder
        column = holder.column
        entity = holder.entity
        simulation = holder.simulation
        debug = simulation.debug
        debug_all = simulation.debug_all
        trace = simulation.trace

        max_nb_cycles = parameters.get('max_nb_cycles')
        extra_params = parameters.get('extra_params')
        if max_nb_cycles is not None:
            simulation.max_nb_cycles = max_nb_cycles

        # Note: Don't compute intersection with column.start & column.end, because holder already does it:
        # output_period = output_period.intersection(periods.instant(column.start), periods.instant(column.end))
        # Note: Don't verify that the function result has already been computed, because this is the task of
        # holder.compute().

        try:
            self.check_for_cycle(period)
            if debug or trace:
                simulation.stack_trace.append(dict(
                    parameters_infos = [],
                    input_variables_infos = [],
                    variable_name = column.name,
                    ))
            if extra_params:
                formula_result = self.base_function(simulation, period, *extra_params)
            else:
                formula_result = self.base_function(simulation, period)
        except CycleError:
            self.clean_cycle_detection_data()
            if max_nb_cycles is None:
                # Re-raise until reaching the first variable called with max_nb_cycles != None in the stack.
                raise
            simulation.max_nb_cycles = None
            return holder.put_in_cache(self.default_values(), period, extra_params)
        except legislations.ParameterNotFound as exc:
            if exc.variable_name is None:
                raise legislations.ParameterNotFound(
                    instant = exc.instant,
                    name = exc.name,
                    variable_name = column.name,
                    )
            else:
                raise
        except:
            log.error(u'An error occurred while calling formula {}@{}<{}> in module {}'.format(
                column.name, entity.key, str(period), self.function.__module__,
                ))
            raise
        else:
            try:
                output_period, array = formula_result
            except ValueError:
                raise ValueError(u'A formula must return "period, array": {}@{}<{}> in module {}'.format(
                    column.name, entity.key, str(period), self.function.__module__,
                    ).encode('utf-8'))
        assert output_period[1] <= period[1] <= output_period.stop, \
            u"Function {}@{}<{}>() --> <{}>{} returns an output period that doesn't include start instant of" \
            u"requested period".format(column.name, entity.key, str(period), str(output_period),
                stringify_array(array)).encode('utf-8')
        assert isinstance(array, np.ndarray), u"Function {}@{}<{}>() --> <{}>{} doesn't return a numpy array".format(
            column.name, entity.key, str(period), str(output_period), array).encode('utf-8')
        entity_count = entity.count
        assert array.size == entity_count, \
            u"Function {}@{}<{}>() --> <{}>{} returns an array of size {}, but size {} is expected for {}".format(
                column.name, entity.key, str(period), str(output_period), stringify_array(array),
                array.size, entity_count, entity.key).encode('utf-8')
        if debug:
            try:
                # cf http://stackoverflow.com/questions/6736590/fast-check-for-nan-in-numpy
                if np.isnan(np.min(array)):
                    nan_count = np.count_nonzero(np.isnan(array))
                    raise NaNCreationError(u"Function {}@{}<{}>() --> <{}>{} returns {} NaN value(s)".format(
                        column.name, entity.key, str(period), str(output_period), stringify_array(array),
                        nan_count).encode('utf-8'))
            except TypeError:
                pass
        if array.dtype != column.dtype:
            array = array.astype(column.dtype)

        if debug or trace:
            variable_infos = (column.name, output_period)
            step = simulation.traceback.get(variable_infos)
            if step is None:
                simulation.traceback[variable_infos] = step = dict(
                    holder = holder,
                    )
            step.update(simulation.stack_trace.pop())
            input_variables_infos = step['input_variables_infos']
            if not debug_all or trace:
                step['default_input_variables'] = has_only_default_input_variables = all(
                    np.all(input_holder.get_array(input_variable_period) == input_holder.column.default)
                    for input_holder, input_variable_period in (
                        (simulation.get_holder(input_variable_name), input_variable_period1)
                        for input_variable_name, input_variable_period1 in input_variables_infos
                        )
                    )
            step['is_computed'] = True
            if debug and (debug_all or not has_only_default_input_variables):
                log.info(u'<=> {}@{}<{}>({}) --> <{}>{}'.format(column.name, entity.key, str(period),
                    simulation.stringify_input_variables_infos(input_variables_infos), str(output_period),
                    stringify_array(array)))

        dated_holder = holder.put_in_cache(array, output_period, extra_params)

        self.clean_cycle_detection_data()
        if max_nb_cycles is not None:
            simulation.max_nb_cycles = None

        return dated_holder

    # Retro-compatibility-layer
    def exec_function(self, simulation, period, *extra_params):

        if self.function.im_func.func_code.co_varnames[0] == 'self':
            return self.function(simulation, period, *extra_params)
        else:
            entity = self.holder.entity
            function = self.function.im_func
            legislation = simulation.legislation_at
            if self.function.im_func.func_code.co_argcount == 2:
                return function(entity, period)
            else:
                return function(entity, period, legislation, *extra_params)

    def filter_role(self, array_or_dated_holder, default = None, entity = None, role = None):
        """Convert a persons array to an entity array, copying only cells of persons having the given role."""
        holder = self.holder
        simulation = holder.simulation
        persons = simulation.persons
        if entity is None:
            entity = holder.entity
        else:
            assert entity in simulation.tax_benefit_system.entities, u"Unknown entity: {}".format(entity).encode('utf-8')

        assert not entity.is_person
        if isinstance(array_or_dated_holder, (holders.DatedHolder, holders.Holder)):
            assert array_or_dated_holder.entity.is_person
            array = array_or_dated_holder.array
            if default is None:
                default = array_or_dated_holder.column.default
        else:
            array = array_or_dated_holder
            assert isinstance(array, np.ndarray), u"Expected a holder or a Numpy array. Got: {}".format(array).encode(
                'utf-8')
            persons_count = persons.count
            assert array.size == persons_count, u"Expected an array of size {}. Got: {}".format(persons_count,
                array.size)
            if default is None:
                default = 0
        entity_index_array = simulation.get_entity(entity).members_entity_id

        assert isinstance(role, int)
        entity_count = entity.count
        target_array = np.empty(entity_count, dtype = array.dtype)
        target_array.fill(default)
        boolean_filter = simulation.get_entity(entity).members_legacy_role == role
        try:
            target_array[entity_index_array[boolean_filter]] = array[boolean_filter]
        except:
            log.error(u'An error occurred while filtering array for role {}[{}] in function {}'.format(
                entity.key, role, holder.column.name))
            raise
        return target_array

    def graph_parameters(self, edges, get_input_variables_and_parameters, nodes, visited):
        """Recursively build a graph of formulas."""
        holder = self.holder
        column = holder.column
        simulation = holder.simulation
        variables_name, parameters_name = get_input_variables_and_parameters(column)
        if variables_name is not None:
            for variable_name in sorted(variables_name):
                variable_holder = simulation.get_or_new_holder(variable_name)
                variable_holder.graph(edges, get_input_variables_and_parameters, nodes, visited)
                edges.append({
                    'from': variable_holder.column.name,
                    'to': column.name,
                    })

    def split_by_roles(self, array_or_dated_holder, default = None, entity = None, roles = None):
        """dispatch a persons array to several entity arrays (one for each role)."""
        holder = self.holder
        simulation = holder.simulation
        persons = simulation.persons
        if entity is None:
            entity = holder.entity
        else:
            assert entity in simulation.tax_benefit_system.entities, u"Unknown entity: {}".format(entity).encode('utf-8')

        assert not entity.is_person
        if isinstance(array_or_dated_holder, (holders.DatedHolder, holders.Holder)):
            assert array_or_dated_holder.entity.is_person
            array = array_or_dated_holder.array
            if default is None:
                default = array_or_dated_holder.column.default
        else:
            array = array_or_dated_holder
            assert isinstance(array, np.ndarray), u"Expected a holder or a Numpy array. Got: {}".format(array).encode(
                'utf-8')
            persons_count = persons.count
            assert array.size == persons_count, u"Expected an array of size {}. Got: {}".format(persons_count,
                array.size)
            if default is None:
                default = 0
        entity_index_array = simulation.get_entity(entity).members_entity_id
        if roles is None:
            # To ensure that existing formulas don't fail, ensure there is always at least 11 roles.
            # roles = range(entity.roles_count)
            roles = range(max(entity.roles_count, 11))
        target_array_by_role = {}
        entity_count = entity.count
        for role in roles:
            target_array_by_role[role] = target_array = np.empty(entity_count, dtype = array.dtype)
            target_array.fill(default)

            boolean_filter = simulation.get_entity(entity).members_legacy_role == role
            try:
                target_array[entity_index_array[boolean_filter]] = array[boolean_filter]
            except:
                log.error(u'An error occurred while filtering array for role {}[{}] in function {}'.format(
                    entity.key, role, holder.column.name))
                raise
        return target_array_by_role

    def sum_by_entity(self, array_or_dated_holder, entity = None, roles = None):
        holder = self.holder
        simulation = holder.simulation
        persons = simulation.persons
        if entity is None:
            entity = holder.entity
        else:
            assert entity in simulation.tax_benefit_system.entities, u"Unknown entity: {}".format(entity).encode('utf-8')

        assert not entity.is_person
        if isinstance(array_or_dated_holder, (holders.DatedHolder, holders.Holder)):
            assert array_or_dated_holder.entity.is_person
            array = array_or_dated_holder.array
        else:
            array = array_or_dated_holder
            assert isinstance(array, np.ndarray), u"Expected a holder or a Numpy array. Got: {}".format(array).encode(
                'utf-8')
            persons_count = persons.count
            assert array.size == persons_count, u"Expected an array of size {}. Got: {}".format(persons_count,
                array.size)

        entity_index_array = simulation.get_entity(entity).members_entity_id

        if roles is None:  # Here we assume we have only one person per role. Not true with new role.
            roles = range(entity.roles_count)
        target_array = np.zeros(entity.count, dtype = array.dtype if array.dtype != np.bool else np.int16)
        for role in roles:
            # TODO: Mettre les filtres en cache dans la simulation
            boolean_filter = simulation.get_entity(entity).members_legacy_role == role
            target_array[entity_index_array[boolean_filter]] += array[boolean_filter]
        return target_array

    def to_json(self, get_input_variables_and_parameters = None, with_input_variables_details = False):
        function = self.function
        if function is None:
            return None
        comments = inspect.getcomments(function)
        doc = inspect.getdoc(function)
        self_json = collections.OrderedDict((
            ('@type', u'SimpleFormula'),
            ('comments', comments.decode('utf-8') if comments is not None else None),
            ('doc', doc.decode('utf-8') if doc is not None else None),
            ))
        if get_input_variables_and_parameters is not None:
            holder = self.holder
            column = holder.column
            simulation = holder.simulation
            variables_name, parameters_name = get_input_variables_and_parameters(column)
            if variables_name:
                if with_input_variables_details:
                    input_variables_json = []
                    for variable_name in sorted(variables_name):
                        variable_holder = simulation.get_or_new_holder(variable_name)
                        variable_column = variable_holder.column
                        input_variables_json.append(collections.OrderedDict((
                            ('entity', variable_holder.entity.key),
                            ('label', variable_column.label),
                            ('name', variable_column.name),
                            )))
                    self_json['input_variables'] = input_variables_json
                else:
                    self_json['input_variables'] = list(variables_name)
            if parameters_name:
                self_json['parameters'] = list(parameters_name)
        return self_json


def calculate_output_add(formula, period):
    return formula.holder.compute_add(period).array


def calculate_output_add_divide(formula, period):
    return formula.holder.compute_add_divide(period).array


def calculate_output_divide(formula, period):
    return formula.holder.compute_divide(period).array


def dated_function(start = None, stop = None):
    """Function decorator used to give start & stop instants to a method of a function in class DatedVariable."""
    def dated_function_decorator(function):
        function.start_instant = periods.instant(start)
        function.stop_instant = periods.instant(stop)
        return function

    return dated_function_decorator


def missing_value(formula, simulation, period):
    if formula.function is not None:
        return formula.function(simulation, period)
    holder = formula.holder
    column = holder.column
    raise ValueError(u"Missing value for variable {} at {}".format(column.name, period))


def neutralize_column(column):
    """Return a new neutralized column (to be used by reforms)."""
    return new_filled_column(
        base_function = requested_period_default_value_neutralized,
        entity = column.entity,
        label = u'[Neutralized]' if column.label is None else u'[Neutralized] {}'.format(column.label),
        reference_column = column,
        scalar = True,
        set_input = set_input_neutralized,
        )


def new_filled_column(base_function = UnboundLocalError, calculate_output = UnboundLocalError,
        cerfa_field = UnboundLocalError, column = UnboundLocalError, comments = UnboundLocalError,
        __doc__ = None, __module__ = None,
        entity = UnboundLocalError, formula_class = UnboundLocalError, is_permanent = UnboundLocalError,
        label = UnboundLocalError, law_reference = UnboundLocalError, start_line_number = UnboundLocalError,
        name = None, reference_column = None, scalar = UnboundLocalError, set_input = UnboundLocalError,
        source_code = UnboundLocalError, source_file_path = UnboundLocalError, start_date = UnboundLocalError,
        stop_date = UnboundLocalError, url = UnboundLocalError, **specific_attributes):
    # Validate arguments.

    if reference_column is not None:
        assert isinstance(reference_column, columns.Column)
        if name is None:
            name = reference_column.name

    assert isinstance(name, unicode)

    if calculate_output is UnboundLocalError:
        calculate_output = None if reference_column is None else reference_column.formula_class.calculate_output

    if cerfa_field is UnboundLocalError:
        cerfa_field = None if reference_column is None else reference_column.cerfa_field
    elif cerfa_field is not None:
        assert isinstance(cerfa_field, (basestring, dict)), cerfa_field

    assert column is not None, """Missing attribute "column" in definition of filled column {}""".format(name)
    if column is UnboundLocalError:
        assert reference_column is not None, """Missing attribute "column" in definition of filled column {}""".format(
            name)
        column = reference_column.empty_clone()
    elif not isinstance(column, columns.Column):
        column = column()
        assert isinstance(column, columns.Column)

    if comments is UnboundLocalError:
        comments = None if reference_column is None else reference_column.formula_class.comments
    elif isinstance(comments, str):
        comments = comments.decode('utf-8')

    assert entity is not None, """Missing attribute "entity" in definition of filled column {}""".format(
        name)
    if entity is UnboundLocalError:
        assert reference_column is not None, \
            """Missing attribute "entity" in definition of filled column {}""".format(name)
        entity = reference_column.entity

    assert formula_class is not None, """Missing attribute "formula_class" in definition of filled column {}""".format(
        name)
    if formula_class is UnboundLocalError:
        assert reference_column is not None, \
            """Missing attribute "formula_class" in definition of filled column {}""".format(name)
        formula_class = reference_column.formula_class.__bases__[0]
    assert issubclass(formula_class, AbstractFormula), formula_class

    if is_permanent is UnboundLocalError:
        is_permanent = False if reference_column is None else reference_column.is_permanent
    else:
        assert is_permanent in (False, True), is_permanent

    if label is UnboundLocalError:
        label = None if reference_column is None else reference_column.label
    else:
        label = None if label is None else unicode(label)

    if law_reference is UnboundLocalError:
        law_reference = None if reference_column is None else reference_column.law_reference
    else:
        assert isinstance(law_reference, (basestring, list))

    if scalar is UnboundLocalError:
        scalar = False if reference_column is None else reference_column.scalar
    else:
        assert scalar in (False, True), scalar

    if start_line_number is UnboundLocalError:
        start_line_number = None if reference_column is None else reference_column.formula_class.start_line_number
    elif isinstance(start_line_number, str):
        start_line_number = start_line_number.decode('utf-8')

    if set_input is UnboundLocalError:
        set_input = None if reference_column is None else reference_column.formula_class.set_input

    if source_code is UnboundLocalError:
        source_code = None if reference_column is None else reference_column.formula_class.source_code
    elif isinstance(source_code, str):
        source_code = source_code.decode('utf-8')

    if source_file_path is UnboundLocalError:
        source_file_path = None if reference_column is None else reference_column.formula_class.source_file_path
    elif isinstance(source_file_path, str):
        source_file_path = source_file_path.decode('utf-8')

    if start_date is UnboundLocalError:
        start_date = None if reference_column is None else reference_column.start
    elif start_date is not None:
        assert isinstance(start_date, datetime.date)

    if stop_date is UnboundLocalError:
        stop_date = None if reference_column is None else reference_column.end
    elif stop_date is not None:
        assert isinstance(stop_date, datetime.date)

    if url is UnboundLocalError:
        url = None if reference_column is None else reference_column.url
    elif url is not None:
        url = unicode(url)

    # Build formula class and column.

    formula_class_attributes = {}
    if __doc__ is not None:
        formula_class_attributes['__doc__'] = __doc__
    if __module__ is not None:
        formula_class_attributes['__module__'] = __module__
    if comments is not None:
        formula_class_attributes['comments'] = comments
    if start_line_number is not None:
        formula_class_attributes['start_line_number'] = start_line_number
    if source_code is not None:
        formula_class_attributes['source_code'] = source_code
    if source_file_path is not None:
        formula_class_attributes['source_file_path'] = source_file_path

    if is_permanent:
        assert base_function in (requested_period_default_value_neutralized, UnboundLocalError), \
            'Unexpected base_function {}'.format(base_function)
        base_function = permanent_default_value
    elif column.is_period_size_independent:
        assert base_function in (missing_value, requested_period_last_value, requested_period_last_or_next_value,
            requested_period_default_value_neutralized, UnboundLocalError), \
            'Unexpected base_function {}'.format(base_function)
        if base_function is UnboundLocalError:
            base_function = requested_period_last_value
    elif base_function is UnboundLocalError:
        base_function = requested_period_default_value
    if base_function is UnboundLocalError:
        assert reference_column is not None \
            and issubclass(reference_column.formula_class, (DatedFormula, SimpleFormula)), \
            """Missing attribute "base_function" in definition of filled column {}""".format(name)
        base_function = reference_column.formula_class.base_function
    else:
        assert base_function is not None, \
            """Missing attribute "base_function" in definition of filled column {}""".format(name)
    formula_class_attributes['base_function'] = base_function

    if calculate_output is not None:
        formula_class_attributes['calculate_output'] = calculate_output

    if set_input is not None:
        formula_class_attributes['set_input'] = set_input

    if issubclass(formula_class, DatedFormula):
        assert not is_permanent
        dated_formulas_class = []
        for function_name, function in specific_attributes.copy().iteritems():
            start_instant = getattr(function, 'start_instant', UnboundLocalError)
            if start_instant is UnboundLocalError:
                # Function is not dated (and may not even be a function). Skip it.
                continue
            stop_instant = function.stop_instant
            if stop_instant is not None:
                assert start_instant <= stop_instant, 'Invalid instant interval for function {}: {} - {}'.format(
                    function_name, start_instant, stop_instant)

            dated_formula_class_attributes = formula_class_attributes.copy()
            dated_formula_class_attributes['function'] = function
            dated_formula_class = type(name.encode('utf-8'), (SimpleFormula,), dated_formula_class_attributes)

            del specific_attributes[function_name]
            dated_formulas_class.append(dict(
                formula_class = dated_formula_class,
                start_instant = start_instant,
                stop_instant = stop_instant,
                ))
        # Sort dated formulas by start instant and add missing stop instants.
        dated_formulas_class.sort(key = lambda dated_formula_class: dated_formula_class['start_instant'])
        for dated_formula_class, next_dated_formula_class in itertools.izip(dated_formulas_class,
                itertools.islice(dated_formulas_class, 1, None)):
            if dated_formula_class['stop_instant'] is None:
                dated_formula_class['stop_instant'] = next_dated_formula_class['start_instant'].offset(-1, 'day')
            else:
                assert dated_formula_class['stop_instant'] < next_dated_formula_class['start_instant'], \
                    "Dated formulas overlap: {} & {}".format(dated_formula_class, next_dated_formula_class)

        # Add dated formulas defined in (optional) reference column when they are not overridden by new dated
        # formulas.
        if reference_column is not None and issubclass(reference_column.formula_class, DatedFormula):
            for reference_dated_formula_class in reference_column.formula_class.dated_formulas_class:
                reference_dated_formula_class = reference_dated_formula_class.copy()
                for dated_formula_class in dated_formulas_class:
                    if reference_dated_formula_class['start_instant'] == dated_formula_class['start_instant'] \
                            and reference_dated_formula_class['stop_instant'] == dated_formula_class[
                                'stop_instant']:
                        break
                    if reference_dated_formula_class['start_instant'] >= dated_formula_class['start_instant'] \
                            and reference_dated_formula_class['start_instant'] < dated_formula_class[
                                'stop_instant']:
                        reference_dated_formula_class['start_instant'] = dated_formula_class['stop_instant'].offset(
                            1, 'day')
                    if reference_dated_formula_class['stop_instant'] > dated_formula_class['start_instant'] \
                            and reference_dated_formula_class['stop_instant'] <= dated_formula_class[
                                'stop_instant']:
                        reference_dated_formula_class['stop_instant'] = dated_formula_class['start_instant'].offset(
                            -1, 'day')
                    if reference_dated_formula_class['start_instant'] > reference_dated_formula_class[
                            'stop_instant']:
                        break
                else:
                    dated_formulas_class.append(reference_dated_formula_class)
            dated_formulas_class.sort(key = lambda dated_formula_class: dated_formula_class['start_instant'])

        formula_class_attributes['dated_formulas_class'] = dated_formulas_class
    else:
        assert issubclass(formula_class, SimpleFormula), formula_class

        function = specific_attributes.pop('function', None)
        if is_permanent:
            assert function is None
        if reference_column is not None and function is None:
            function = reference_column.formula_class.function
        formula_class_attributes['function'] = function

    # Ensure that all attributes defined in ConversionColumn class are used.
    assert not specific_attributes, 'Unexpected attributes in definition of variable "{}": {!r}'.format(name,
        ', '.join(sorted(specific_attributes.iterkeys())))

    formula_class = type(name.encode('utf-8'), (formula_class,), formula_class_attributes)

    # Fill column attributes.
    if cerfa_field is not None:
        column.cerfa_field = cerfa_field
    if stop_date is not None:
        column.end = stop_date
    column.entity = entity
    column.formula_class = formula_class
    if is_permanent:
        column.is_permanent = True
    column.label = label
    column.law_reference = law_reference
    column.name = name
    if scalar:
        column.scalar = True
    if start_date is not None:
        column.start = start_date
    if url is not None:
        column.url = url

    return column


def set_input_dispatch_by_period(formula, period, array):
    holder = formula.holder
    holder.put_in_cache(array, period)
    period_size = period.size
    period_unit = period.unit
    if period_unit == u'year' or period_size > 1:
        after_instant = period.start.offset(period_size, period_unit)
        if period_size > 1:
            sub_period = period.start.period(period_unit)
            while sub_period.start < after_instant:
                existing_array = holder.get_array(sub_period)
                if existing_array is None:
                    holder.put_in_cache(array, sub_period)
                else:
                    # The array of the current sub-period is reused for the next ones.
                    array = existing_array
                sub_period = sub_period.offset(1)
        if period_unit == u'year':
            month = period.start.period(u'month')
            while month.start < after_instant:
                existing_array = holder.get_array(month)
                if existing_array is None:
                    holder.put_in_cache(array, month)
                else:
                    # The array of the current sub-period is reused for the next ones.
                    array = existing_array
                month = month.offset(1)


def set_input_divide_by_period(formula, period, array):
    holder = formula.holder
    holder.put_in_cache(array, period)
    period_size = period.size
    period_unit = period.unit
    if period_unit == u'year' or period_size > 1:
        after_instant = period.start.offset(period_size, period_unit)
        if period_size > 1:
            remaining_array = array.copy()
            sub_period = period.start.period(period_unit)
            sub_periods_count = period_size
            while sub_period.start < after_instant:
                existing_array = holder.get_array(sub_period)
                if existing_array is not None:
                    remaining_array -= existing_array
                    sub_periods_count -= 1
                sub_period = sub_period.offset(1)
            if sub_periods_count > 0:
                divided_array = remaining_array / sub_periods_count
                sub_period = period.start.period(period_unit)
                while sub_period.start < after_instant:
                    if holder.get_array(sub_period) is None:
                        holder.put_in_cache(divided_array, sub_period)
                    sub_period = sub_period.offset(1)
        if period_unit == u'year':
            remaining_array = array.copy()
            month = period.start.period(u'month')
            months_count = 12 * period_size
            while month.start < after_instant:
                existing_array = holder.get_array(month)
                if existing_array is not None:
                    remaining_array -= existing_array
                    months_count -= 1
                month = month.offset(1)
            if months_count > 0:
                divided_array = remaining_array / months_count
                month = period.start.period(u'month')
                while month.start < after_instant:
                    if holder.get_array(month) is None:
                        holder.put_in_cache(divided_array, month)
                    month = month.offset(1)


def set_input_neutralized(formula, period, array):
    pass
