# -*- coding: utf-8 -*-


import warnings
from os import linesep
import tempfile
import logging

import dpath
import numpy as np

import periods
from commons import empty_clone, stringify_array
from .parameters import ParameterNotFound
from tracers import Tracer
from .indexed_enums import Enum, EnumArray


log = logging.getLogger(__name__)


# Exceptions


class NaNCreationError(Exception):
    pass


class CycleError(Exception):
    pass


class Simulation(object):
    _parameters_at_instant_cache = None
    debug = False
    period = None
    baseline_parameters_at_instant_cache = None
    steps_count = 1
    tax_benefit_system = None
    trace = False

    def __init__(
            self,
            debug = False,
            period = None,
            tax_benefit_system = None,
            trace = False,
            opt_out_cache = False,
            simulation_json = None,
            memory_config = None,
            ):
        """
            If a simulation_json is given, initilalises a simulation from a JSON dictionnary.

            This way of initialising a simulation, still under experimentation, aims at replacing the initialisation from `scenario.make_json_or_python_to_attributes`.

            If no simulation_json is given, initilalises an empty simulation.
        """
        self.tax_benefit_system = tax_benefit_system
        assert tax_benefit_system is not None
        if period:
            assert isinstance(period, periods.Period)
        self.period = period

        # To keep track of the values (formulas and periods) being calculated to detect circular definitions.
        # See use in formulas.py.
        # The data structure of requested_periods_by_variable_name is: {variable_name: [period1, period2]}
        self.requested_periods_by_variable_name = {}
        self.max_nb_cycles = None

        self.debug = debug
        self.trace = trace or self.debug
        if self.trace:
            self.tracer = Tracer()
        else:
            self.tracer = None
        self.opt_out_cache = opt_out_cache

        # Note: Since simulations are short-lived and must be fast, don't use weakrefs for cache.
        self._parameters_at_instant_cache = {}
        self.baseline_parameters_at_instant_cache = {}
        self.memory_config = memory_config
        self._data_storage_dir = None
        self.instantiate_entities(simulation_json)

    def instantiate_entities(self, simulation_json):
        if simulation_json:
            check_type(simulation_json, dict, ['error'])
            allowed_entities = set(entity_class.plural for entity_class in self.tax_benefit_system.entities)
            unexpected_entities = [entity for entity in simulation_json if entity not in allowed_entities]
            if unexpected_entities:
                unexpected_entity = unexpected_entities[0]
                raise SituationParsingError([unexpected_entity],
                    'This entity is not defined in the loaded tax and benefit system. The defined entities are {}.'.format(
                        ', '.join(allowed_entities)).encode('utf-8')
                    )
            persons_json = simulation_json.get(self.tax_benefit_system.person_entity.plural, None)

            if not persons_json:
                raise SituationParsingError([self.tax_benefit_system.person_entity.plural],
                    u'No {0} found. At least one {0} must be defined to run a simulation.'.format(self.tax_benefit_system.person_entity.key))
            self.persons = self.tax_benefit_system.person_entity(self, persons_json)
        else:
            self.persons = self.tax_benefit_system.person_entity(self)

        self.entities = {self.persons.key: self.persons}
        setattr(self, self.persons.key, self.persons)  # create shortcut simulation.person (for instance)

        for entity_class in self.tax_benefit_system.group_entities:
            if simulation_json:
                entities_json = simulation_json.get(entity_class.plural)
                entities = entity_class(self, entities_json or {})
            else:
                entities = entity_class(self)
            self.entities[entity_class.key] = entities
            setattr(self, entity_class.key, entities)  # create shortcut simulation.household (for instance)

    @property
    def data_storage_dir(self):
        """
        Temporary folder used to store intermediate calculation data in case the memory is saturated
        """
        if self._data_storage_dir is None:
            self._data_storage_dir = tempfile.mkdtemp(prefix = "openfisca_")
            log.warn((
                u"Intermediate results will be stored on disk in {} in case of memory overflow. "
                u"You should remove this directory once you're done with your simulation."
                ).format(self._data_storage_dir).encode('utf-8'))
        return self._data_storage_dir

    def calculate(self, variable_name, period, **parameters):
        entity = self.get_variable_entity(variable_name)
        holder = entity.get_holder(variable_name)
        variable = self.tax_benefit_system.get_variable(variable_name)

        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)

        if self.trace:
            self.tracer.record_calculation_start(variable.name, period, **parameters)

        check_period_consistency(period, variable)

        extra_params = parameters.get('extra_params', ())

        # First look for a value already cached
        cached_array = holder.get_from_cache(period, extra_params)
        if cached_array is not None:
            if self.trace:
                self.tracer.record_calculation_end(variable.name, period, cached_array, **parameters)
            return cached_array

        max_nb_cycles = parameters.get('max_nb_cycles')
        if max_nb_cycles is not None:
            self.max_nb_cycles = max_nb_cycles

        try:
            self.check_for_cycle(variable, period)

            # First, check if there is a formula to use
            formula = variable.get_formula(period)
            if formula:
                parameters_at = self.parameters_at
                if formula.func_code.co_argcount == 2:
                    array = formula(entity, period)
                else:
                    array = formula(entity, period, parameters_at, *extra_params)
            else:
                # If not, use a base function
                array = variable.base_function(holder, period, *extra_params)

        except CycleError:
            self.clean_cycle_detection_data(variable.name)
            if max_nb_cycles is None:
                if self.trace:
                    self.tracer.record_calculation_abortion(variable.name, period, **parameters)
                # Re-raise until reaching the first variable called with max_nb_cycles != None in the stack.
                raise
            self.max_nb_cycles = None
            array = holder.default_array()
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
            log.error(u'An error occurred while calling formula {}@{}<{}>.'.format(
                variable.name, entity.key, str(period)
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
        if self.debug:
            try:
                # cf https://stackoverflow.com/questions/6736590/fast-check-for-nan-in-numpy
                if np.isnan(np.min(array)):
                    nan_count = np.count_nonzero(np.isnan(array))
                    raise NaNCreationError(u"Function {}@{}<{}>() --> <{}>{} returns {} NaN value(s)".format(
                        variable.name, entity.key, str(period), str(period), stringify_array(array),
                        nan_count).encode('utf-8'))
            except TypeError:
                pass

        if variable.value_type == Enum and not isinstance(array, EnumArray):
            array = variable.possible_values.encode(array)

        if array.dtype != variable.dtype:
            array = array.astype(variable.dtype)

        self.clean_cycle_detection_data(variable.name)
        if max_nb_cycles is not None:
            self.max_nb_cycles = None

        holder.put_in_cache(array, period, extra_params)
        if self.trace:
            self.tracer.record_calculation_end(variable.name, period, array, **parameters)

        return array

    def calculate_add(self, variable_name, period, **parameters):
        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)
        holder = self.get_variable_entity(variable_name).get_holder(variable_name)

        # Check that the requested period matches definition_period
        if holder.variable.definition_period == periods.YEAR and period.unit == periods.MONTH:
            raise ValueError(u'Unable to compute variable {0} for period {1} : {0} can only be computed for year-long periods. You can use the DIVIDE option to get an estimate of {0} by dividing the yearly value by 12, or change the requested period to "period.this_year".'.format(
                holder.variable.name,
                period,
                ).encode('utf-8'))

        if holder.variable.definition_period == periods.MONTH:
            variable_definition_period = periods.MONTH
        elif holder.variable.definition_period == periods.YEAR:
            variable_definition_period = periods.YEAR
        else:
            raise ValueError(u'Unable to sum constant variable {} over period {} : only variables defined monthly or yearly can be summed over time.'.format(
                holder.variable.name,
                period).encode('utf-8'))

        after_instant = period.start.offset(period.size, period.unit)
        sub_period = period.start.period(variable_definition_period)
        array = None
        while sub_period.start < after_instant:
            dated_array = self.calculate(variable_name, period = sub_period, **parameters)
            if array is None:
                array = dated_array.copy()
            else:
                array += dated_array
            sub_period = sub_period.offset(1)

        return array

    def calculate_divide(self, variable_name, period, **parameters):
        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)
        holder = self.get_variable_entity(variable_name).get_holder(variable_name)

        # Check that the requested period matches definition_period
        if holder.variable.definition_period != periods.YEAR:
            raise ValueError(u'Unable to divide the value of {} over time (on period {}) : only variables defined yearly can be divided over time.'.format(
                variable_name,
                period).encode('utf-8'))

        if period.size != 1:
            raise ValueError("DIVIDE option can only be used for a one-year or a one-month requested period")

        if period.unit == periods.MONTH:
            computation_period = period.this_year
            return self.calculate(variable_name, period = computation_period, **parameters) / 12.
        elif period.unit == periods.YEAR:
            return self.calculate(variable_name, period, **parameters)

        raise ValueError(u'Unable to divide the value of {} to match the period {}.'.format(
            variable_name,
            period).encode('utf-8'))

    def calculate_output(self, variable_name, period):
        """Calculate the value using calculate_output hooks in formula classes."""

        variable = self.tax_benefit_system.get_variable(variable_name, check_existence = True)

        if variable.calculate_output is None:
            return self.calculate(variable_name, period)

        return variable.calculate_output(self, variable_name, period)

    def clone(self, debug = False, trace = False):
        """Copy the simulation just enough to be able to run the copy without modifying the original simulation."""
        new = empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.iteritems():
            if key not in ('debug', 'trace', 'tracer'):
                new_dict[key] = value

        new.persons = self.persons.clone(new)
        setattr(new, new.persons.key, new.persons)
        new.entities = {new.persons.key: new.persons}

        for entity_class in self.tax_benefit_system.group_entities:
            entity = self.entities[entity_class.key].clone(new)
            new.entities[entity.key] = entity
            setattr(new, entity_class.key, entity)  # create shortcut simulation.household (for instance)

        if debug:
            new_dict['debug'] = True
        if trace:
            new_dict['trace'] = True
        if debug or trace:
            if self.debug or self.trace:
                new_dict['tracer'] = self.tracer.clone()
            else:
                new_dict['tracer'] = Tracer()

        return new

    def get_array(self, variable_name, period):
        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)
        return self.get_variable_entity(variable_name).get_holder(variable_name).get_array(period)

    def _get_parameters_at_instant(self, instant):
        parameters_at_instant = self._parameters_at_instant_cache.get(instant)
        if parameters_at_instant is None:
            parameters_at_instant = self.tax_benefit_system.get_parameters_at_instant(instant)
            self._parameters_at_instant_cache[instant] = parameters_at_instant
        return parameters_at_instant

    def get_holder(self, variable_name, default = UnboundLocalError):
        warnings.warn(
            u"The simulation.get_holder method has been deprecated. "
            u"Please use entity.get_holder instead.",
            Warning
            )
        variable = self.tax_benefit_system.get_variable(variable_name, check_existence = True)
        entity = self.entities[variable.entity.key]
        holder = entity._holders.get(variable_name)
        if holder:
            return holder
        if default is UnboundLocalError:
            raise KeyError(variable_name)
        return default

    def _get_baseline_parameters_at_instant(self, instant):
        baseline_parameters_at_instant = self._baseline_parameters_at_instant_cache.get(instant)
        if baseline_parameters_at_instant is None:
            baseline_parameters_at_instant = self.tax_benefit_system._get_baseline_parameters_at_instant(
                instant = instant,
                traced_simulation = self if self.trace else None,
                )
            self.baseline_parameters_at_instant_cache[instant] = baseline_parameters_at_instant
        return baseline_parameters_at_instant

    def parameters_at(self, instant, use_baseline = False):
        if isinstance(instant, periods.Period):
            instant = instant.start
        assert isinstance(instant, periods.Instant), "Expected an Instant (e.g. Instant((2017, 1, 1)) ). Got: {}.".format(instant)
        if use_baseline:
            return self._get_baseline_parameters_at_instant(instant)
        return self._get_parameters_at_instant(instant)

    # Fixme: to rewrite
    def to_input_variables_json(self):
        return None

    def get_variable_entity(self, variable_name):
        variable = self.tax_benefit_system.get_variable(variable_name, check_existence = True)
        return self.get_entity(variable.entity)

    def get_entity(self, entity_type = None, plural = None):
        if entity_type:
            return self.entities[entity_type.key]
        if plural:
            return [entity for entity in self.entities.values() if entity.plural == plural][0]

    def get_memory_usage(self, variables = None):
        result = dict(
            total_nb_bytes = 0,
            by_variable = {}
            )
        for entity in self.entities.itervalues():
            entity_memory_usage = entity.get_memory_usage(variables = variables)
            result['total_nb_bytes'] += entity_memory_usage['total_nb_bytes']
            result['by_variable'].update(entity_memory_usage['by_variable'])
        return result

    def check_for_cycle(self, variable, period):
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
        requested_periods_by_variable_name = self.requested_periods_by_variable_name
        variable_name = variable.name
        if variable_name in requested_periods_by_variable_name:
            # Make sure the formula doesn't call itself for the same period it is being called for.
            # It would be a pure circular definition.
            requested_periods = requested_periods_by_variable_name[variable_name]
            assert period not in requested_periods and (variable.definition_period != periods.ETERNITY), get_error_message()
            if self.max_nb_cycles is None or len(requested_periods) > self.max_nb_cycles:
                message = get_error_message()
                if self.max_nb_cycles is None:
                    message += ' Hint: use "max_nb_cycles = 0" to get a default value, or "= N" to allow N cycles.'
                raise CycleError(message)
            else:
                requested_periods.append(period)
        else:
            requested_periods_by_variable_name[variable_name] = [period]

    def clean_cycle_detection_data(self, variable_name):
        """
        When the value of a formula have been computed, remove the period from
        requested_periods_by_variable_name[variable_name] and delete the latter if empty.
        """

        requested_periods_by_variable_name = self.requested_periods_by_variable_name
        if variable_name in requested_periods_by_variable_name:
            requested_periods_by_variable_name[variable_name].pop()
            if len(requested_periods_by_variable_name[variable_name]) == 0:
                del requested_periods_by_variable_name[variable_name]


def check_type(input, type, path = []):
    json_type_map = {
        dict: "Object",
        list: "Array",
        basestring: "String"
        }

    if not isinstance(input, type):
        raise SituationParsingError(path,
            u"Invalid type: must be of type '{}'.".format(json_type_map[type]))


class SituationParsingError(Exception):
    def __init__(self, path, message, code = None):
        self.error = {}
        dpath_path = '/'.join(path)
        message = message.strip(linesep).replace(linesep, ' ')
        dpath.util.new(self.error, dpath_path, message)
        self.code = code
        Exception.__init__(self, self.error)


def check_period_consistency(period, variable):
    """
        Check that a period matches the variable definition_period
    """
    if variable.definition_period == periods.ETERNITY:
        return  # For variables which values are constant in time, all periods are accepted

    if variable.definition_period == periods.MONTH and period.unit != periods.MONTH:
        raise ValueError(u'Unable to compute variable {0} for period {1} : {0} must be computed for a whole month. You can use the ADD option to sum {0} over the requested period, or change the requested period to "period.first_month".'.format(
            variable.name,
            period
            ).encode('utf-8'))

    if variable.definition_period == periods.YEAR and period.unit != periods.YEAR:
        raise ValueError(u'Unable to compute variable {0} for period {1} : {0} must be computed for a whole year. You can use the DIVIDE option to get an estimate of {0} by dividing the yearly value by 12, or change the requested period to "period.this_year".'.format(
            variable.name,
            period
            ).encode('utf-8'))

    if period.size != 1:
        raise ValueError(u'Unable to compute variable {0} for period {1} : {0} must be computed for a whole {2}. You can use the ADD option to sum {0} over the requested period.'.format(
            variable.name,
            period,
            'month' if variable.definition_period == periods.MONTH else 'year'
            ).encode('utf-8'))


def calculate_output_add(simulation, variable_name, period):
    return simulation.calculate_add(variable_name, period)


def calculate_output_divide(simulation, variable_name, period):
    return simulation.calculate_divide(variable_name, period)
