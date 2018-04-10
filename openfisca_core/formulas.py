# -*- coding: utf-8 -*-


from __future__ import division

import collections
import inspect
import datetime
import logging
import warnings
from os import linesep

import numpy as np

from . import holders, periods
from .parameters import ParameterNotFound
from .periods import MONTH, YEAR, ETERNITY
from .commons import empty_clone, stringify_array
from .indexed_enums import Enum, EnumArray


log = logging.getLogger(__name__)


ADD = 'add'
DIVIDE = 'divide'



# Exceptions


class NaNCreationError(Exception):
    pass


class CycleError(Exception):
    pass

# Formulas


class Formula(object):
    """
    An OpenFisca Formula for a Variable.
    Such a Formula might have different behaviors according to the time period.
    """
    comments = None
    holder = None
    start_line_number = None
    source_code = None
    source_file_path = None
    base_function = None  # Class attribute. Overridden by subclasses
    dated_formulas = None  # A list of dictionaries containing a formula instance and a start instant
    dated_formulas_class = None  # A list of dictionaries containing a formula class and a start instant

    def __init__(self, holder = None):
        assert holder is not None
        self.holder = holder

        if self.dated_formulas_class is not None:
            self.dated_formulas = [
                dict(
                    formula = dated_formula_class['formula_class'](holder = holder),
                    start_instant = dated_formula_class['start_instant'],
                    )
                for dated_formula_class in self.dated_formulas_class
                ]

    def clone(self, holder, keys_to_skip = None):
        """Copy the formula just enough to be able to run a new simulation without modifying the original simulation."""
        new = empty_clone(self)
        new_dict = new.__dict__

        if keys_to_skip is None:
            keys_to_skip = set()
        keys_to_skip.add('dated_formulas')
        keys_to_skip.add('holder')

        for key, value in self.__dict__.iteritems():
            if key not in keys_to_skip:
                new_dict[key] = value
        new_dict['holder'] = holder

        if self.dated_formulas is not None:
            new.dated_formulas = [
                {
                    key: value.clone(holder) if key == 'formula' else value
                    for key, value in dated_formula.iteritems()
                    }
                for dated_formula in self.dated_formulas
                ]

        return new

    def calculate_output(self, period):
        return self.holder.compute(period).array

    def default_values(self):
        '''Return a new NumPy array which length is the entity count, filled with default values.'''
        return self.zeros() + self.holder.variable.default_value

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

    # Roles & Entities dispatch helpers

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
                        array_or_dated_holder.variable.entity.key).encode('utf-8')
            array = array_or_dated_holder.array
            if default is None:
                default = array_or_dated_holder.variable.default_value
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
                    entity.key, role, holder.variable.name))
                raise
        return target_array

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
                default = array_or_dated_holder.variable.default_value
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
                entity.key, role, holder.variable.name))
            raise
        return target_array

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
                default = array_or_dated_holder.variable.default_value
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
                    entity.key, role, holder.variable.name))
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

    @classmethod
    def at_instant(cls, instant, default = UnboundLocalError):
        assert isinstance(instant, periods.Instant)
        for dated_formula_class in cls.dated_formulas_class:
            start_instant = dated_formula_class['start_instant']
            if (start_instant is None or start_instant <= instant):
                return dated_formula_class['formula_class']
        if default is UnboundLocalError:
            raise KeyError(instant)
        return default

    def check_for_cycle(self, period):
        """
        Return a boolean telling if the current variable has already been called without being allowed by
        the parameter max_nb_cycles of the calculate method.
        """
        def get_error_message():
            return u'Circular definition detected on formula {}<{}>. Formulas and periods involved: {}.'.format(
                variable.name,
                period,
                u', '.join(sorted(set(
                    u'{}<{}>'.format(variable_name, period2)
                    for variable_name, periods in requested_periods_by_variable_name.iteritems()
                    for period2 in periods
                    ))).encode('utf-8'),
                )
        simulation = self.holder.simulation
        requested_periods_by_variable_name = simulation.requested_periods_by_variable_name
        variable = self.holder.variable
        variable_name = variable.name
        if variable_name in requested_periods_by_variable_name:
            # Make sure the formula doesn't call itself for the same period it is being called for.
            # It would be a pure circular definition.
            requested_periods = requested_periods_by_variable_name[variable_name]
            assert period not in requested_periods and (variable.definition_period != ETERNITY), get_error_message()
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
        variable = self.holder.variable
        variable_name = variable.name
        requested_periods_by_variable_name = simulation.requested_periods_by_variable_name
        if variable_name in requested_periods_by_variable_name:
            requested_periods_by_variable_name[variable_name].pop()
            if len(requested_periods_by_variable_name[variable_name]) == 0:
                del requested_periods_by_variable_name[variable_name]

    def compute(self, period, **parameters):
        """
        Called by `Holder.compute` only when no value is found in cache.
        Return a DatedHolder after checking for cycles in formula.
        """
        holder = self.holder
        variable = holder.variable
        entity = holder.entity
        simulation = holder.simulation
        debug = simulation.debug

        assert (period is not None) or (variable.definition_period == ETERNITY)

        max_nb_cycles = parameters.get('max_nb_cycles')
        extra_params = parameters.get('extra_params')
        if max_nb_cycles is not None:
            simulation.max_nb_cycles = max_nb_cycles

        # Note: Don't compute intersection with variable.start & variable.end, because holder already does it:
        # output_period = output_period.intersection(periods.instant(variable.start), periods.instant(variable.end))
        # Note: Don't verify that the function result has already been computed, because this is the task of
        # holder.compute().

        try:
            self.check_for_cycle(period)
            if extra_params:
                array = self.base_function(simulation, period, *extra_params)
            else:
                array = self.base_function(simulation, period)
        except CycleError:
            self.clean_cycle_detection_data()
            if max_nb_cycles is None:
                if simulation.trace:
                    simulation.tracer.record_calculation_abortion(variable.name, period, **parameters)
                # Re-raise until reaching the first variable called with max_nb_cycles != None in the stack.
                raise
            simulation.max_nb_cycles = None
            return holder.put_in_cache(self.default_values(), period, extra_params)
        except ParameterNotFound as exc:
            if exc.variable_name is None:
                raise ParameterNotFound(
                    instant_str = exc.instant_str,
                    name = exc.name,
                    variable_name = variable.name,
                    )
            else:
                raise
        except:
            log.error(u'An error occurred while calling formula {}@{}<{}> in module {}'.format(
                variable.name, entity.key, str(period), self.__module__,
                ))
            raise

        assert isinstance(array, np.ndarray), (linesep.join([
            u"You tried to compute the formula '{0}' for the period '{1}'.".format(variable.name, str(period)).encode('utf-8'),
            u"The formula '{0}@{1}' should return a Numpy array;".format(variable.name, str(period)).encode('utf-8'),
            u"instead it returned '{0}' of '{1}'.".format(array, type(array)).encode('utf-8'),
            u"Learn more about Numpy arrays and vectorial computing:",
            u"<http://openfisca.org/doc/coding-the-legislation/25_vectorial_computing.html.>"
            ]))
        entity_count = entity.count
        assert array.size == entity_count, \
            u"Function {}@{}<{}>() --> <{}>{} returns an array of size {}, but size {} is expected for {}".format(
                variable.name, entity.key, str(period), str(period), stringify_array(array),
                array.size, entity_count, entity.key).encode('utf-8')
        if debug:
            try:
                # cf https://stackoverflow.com/questions/6736590/fast-check-for-nan-in-numpy
                if np.isnan(np.min(array)):
                    nan_count = np.count_nonzero(np.isnan(array))
                    raise NaNCreationError(u"Function {}@{}<{}>() --> <{}>{} returns {} NaN value(s)".format(
                        variable.name, entity.key, str(period), str(period), stringify_array(array),
                        nan_count).encode('utf-8'))
            except TypeError:
                pass

        if self.holder.variable.value_type == Enum and not isinstance(array, EnumArray):
            array = self.holder.variable.possible_values.encode(array)

        if array.dtype != variable.dtype:
            array = array.astype(variable.dtype)

        self.clean_cycle_detection_data()
        if max_nb_cycles is not None:
            simulation.max_nb_cycles = None

        return holders.DatedHolder(self.holder, period, array, extra_params)

    def find_function(self, period):
        """
        Finds the last active formula for the time interval [period starting date, variable end attribute].
        """
        end = self.holder.variable.end
        if end and period.start.date > end:
            return None

        # All formulas are already dated (with default start date in absence of user date)
        for dated_formula in reversed(self.dated_formulas):
            start = dated_formula['start_instant'].date

            if period.start.date >= start:
                return dated_formula['formula'].formula

        return None

    def exec_function(self, simulation, period, *extra_params):
        """
        Calls the right Variable's dated function for current period and returns a NumPy array.
        """

        function = self.find_function(period)
        entity = self.holder.entity
        function = function.im_func
        parameters_at = simulation.parameters_at
        if function.func_code.co_argcount == 2:
            return function(entity, period)
        else:
            return function(entity, period, parameters_at, *extra_params)

    def graph_parameters(self, edges, get_input_variables_and_parameters, nodes, visited):
        """Recursively build a graph of formulas."""
        if self.dated_formulas is not None:
            for dated_formula in self.dated_formulas:
                dated_formula['formula'].graph_parameters(edges, get_input_variables_and_parameters, nodes, visited)
        else:
            holder = self.holder
            variable = holder.variable
            simulation = holder.simulation
            variables_name, parameters_name = get_input_variables_and_parameters(variable)
            if variables_name is not None:
                for variable_name in sorted(variables_name):
                    variable_holder = simulation.get_or_new_holder(variable_name)
                    variable_holder.graph(edges, get_input_variables_and_parameters, nodes, visited)
                    edges.append({
                        'from': variable_holder.variable.name,
                        'to': variable.name,
                        })

    def formula_to_json(self, function, get_input_variables_and_parameters = None, with_input_variables_details = False):
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
            variable = holder.variable
            simulation = holder.simulation
            variables_name, parameters_name = get_input_variables_and_parameters(variable)
            if variables_name:
                if with_input_variables_details:
                    input_variables_json = []
                    for variable_name in sorted(variables_name):
                        variable_holder = simulation.get_variable_entity(variable_name).get_holder(variable_name)
                        variable_variable = variable_holder.variable
                        input_variables_json.append(collections.OrderedDict((
                            ('entity', variable_holder.entity.key),
                            ('label', variable_variable.label),
                            ('name', variable_variable.name),
                            )))
                    self_json['input_variables'] = input_variables_json
                else:
                    self_json['input_variables'] = list(variables_name)
            if parameters_name:
                self_json['parameters'] = list(parameters_name)
        return self_json

    def to_json(self, get_input_variables_and_parameters = None, with_input_variables_details = False):
        return collections.OrderedDict((
            ('@type', u'DatedFormula'),
            ('dated_formulas', [
                dict(
                    formula = self.formula_to_json(
                        dated_formula['formula'].formula,
                        get_input_variables_and_parameters = get_input_variables_and_parameters,
                        with_input_variables_details = with_input_variables_details,
                        ),
                    start_instant = (None if dated_formula['start_instant'] is None
                        else str(dated_formula['start_instant'])),
                    stop_instant = (None if dated_formula.get('stop_instant') is None
                        else str(dated_formula['stop_instant'])),
                    )
                for dated_formula in self.dated_formulas
                ]),
            ))


def calculate_output_add(formula, period):
    return formula.holder.compute_add(period).array


def calculate_output_divide(formula, period):
    return formula.holder.compute_divide(period).array


def get_neutralized_variable(variable):
    """
        Return a new neutralized variable (to be used by reforms).
        A neutralized variable always returns its default value, and does not cache anything.
    """
    result = variable.clone()
    result.is_neutralized = True
    result.label = u'[Neutralized]' if variable.label is None else u'[Neutralized] {}'.format(variable.label),
    result.set_input = set_input_neutralized
    result.formula.set_input = set_input_neutralized

    return result


def set_input_dispatch_by_period(formula, period, array):
    holder = formula.holder
    period_size = period.size
    period_unit = period.unit

    if formula.holder.variable.definition_period == MONTH:
        cached_period_unit = periods.MONTH
    elif formula.holder.variable.definition_period == YEAR:
        cached_period_unit = periods.YEAR
    else:
        raise ValueError('set_input_dispatch_by_period can be used only for yearly or monthly variables.')

    after_instant = period.start.offset(period_size, period_unit)

    # Cache the input data, skipping the existing cached months
    sub_period = period.start.period(cached_period_unit)
    while sub_period.start < after_instant:
        existing_array = holder.get_array(sub_period)
        if existing_array is None:
            holder.put_in_cache(array, sub_period)
        else:
            # The array of the current sub-period is reused for the next ones.
            # TODO: refactor or document this behavior
            array = existing_array
        sub_period = sub_period.offset(1)


def set_input_divide_by_period(formula, period, array):
    holder = formula.holder
    period_size = period.size
    period_unit = period.unit

    if formula.holder.variable.definition_period == MONTH:
        cached_period_unit = periods.MONTH
    elif formula.holder.variable.definition_period == YEAR:
        cached_period_unit = periods.YEAR
    else:
        raise ValueError('set_input_divide_by_period can be used only for yearly or monthly variables.')

    after_instant = period.start.offset(period_size, period_unit)

    # Count the number of elementary periods to change, and the difference with what is already known.
    remaining_array = array.copy()
    sub_period = period.start.period(cached_period_unit)
    sub_periods_count = 0
    while sub_period.start < after_instant:
        existing_array = holder.get_array(sub_period)
        if existing_array is not None:
            remaining_array -= existing_array
        else:
            sub_periods_count += 1
        sub_period = sub_period.offset(1)

    # Cache the input data
    if sub_periods_count > 0:
        divided_array = remaining_array / sub_periods_count
        sub_period = period.start.period(cached_period_unit)
        while sub_period.start < after_instant:
            if holder.get_array(sub_period) is None:
                holder.put_in_cache(divided_array, sub_period)
            sub_period = sub_period.offset(1)
    elif not (remaining_array == 0).all():
        raise ValueError(u"Inconsistent input: variable {0} has already been set for all months contained in period {1}, and value {2} provided for {1} doesn't match the total ({3}). This error may also be thrown if you try to call set_input twice for the same variable and period.".format(holder.variable.name, period, array, array - remaining_array).encode('utf-8'))


def set_input_neutralized(formula, period, array):
    warnings.warn(
        u"You cannot set a value for the variable {}, as it has been neutralized. The value you provided ({}) will be ignored."
        .format(formula.holder.variable.name, array).encode('utf-8'),
        Warning
        )
