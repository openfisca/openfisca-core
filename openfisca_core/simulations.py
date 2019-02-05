# -*- coding: utf-8 -*-


from os import linesep
import tempfile
import logging

import numpy as np

from openfisca_core import periods
from openfisca_core.commons import empty_clone, stringify_array
from openfisca_core.tracers import Tracer, TracingParameterNodeAtInstant
from openfisca_core.indexed_enums import Enum, EnumArray


log = logging.getLogger(__name__)


# Exceptions


class NaNCreationError(Exception):
    pass


class CycleError(Exception):
    pass


class SpiralError(Exception):
    pass


class Simulation(object):
    """
        Represents a simulation, and handles the calculation logic
    """

    def __init__(
            self,
            tax_benefit_system,
            entities_instances = None
            ):
        """
            This constructor is reserved for internal use; see :any:`SimulationBuilder`,
            which is the preferred way to obtain a Simulation initialized with a consistent
            set of Entities.
        """
        self.tax_benefit_system = tax_benefit_system
        assert tax_benefit_system is not None

        self.entities = entities_instances
        self.persons = self.entities[tax_benefit_system.person_entity.key]
        self.link_to_entities_instances()
        self.create_shortcuts()

        # To keep track of the values (formulas and periods) being calculated to detect circular definitions.
        # The data structure of computation_stack is:
        # [('variable_name', 'period1'), ('variable_name', 'period2')]
        self.computation_stack = []
        self.invalidated_caches = set()

        self.debug = False
        self.trace = False
        self.opt_out_cache = False

        # controls the spirals detection; check for performance impact if > 1
        self.max_spiral_loops = 1
        self.memory_config = None
        self._data_storage_dir = None

    @property
    def trace(self):
        return self._trace

    @trace.setter
    def trace(self, trace):
        self._trace = trace
        if trace:
            self.tracer = Tracer()
        else:
            self.tracer = None

    def link_to_entities_instances(self):
        for _key, entity_instance in self.entities.items():
            entity_instance.simulation = self

    def create_shortcuts(self):
        for _key, entity_instance in self.entities.items():
            # create shortcut simulation.person and simulation.household (for instance)
            setattr(self, entity_instance.key, entity_instance)

    @property
    def data_storage_dir(self):
        """
        Temporary folder used to store intermediate calculation data in case the memory is saturated
        """
        if self._data_storage_dir is None:
            self._data_storage_dir = tempfile.mkdtemp(prefix = "openfisca_")
            log.warn((
                "Intermediate results will be stored on disk in {} in case of memory overflow. "
                "You should remove this directory once you're done with your simulation."
                ).format(self._data_storage_dir).encode('utf-8'))
        return self._data_storage_dir

    # ----- Calculation methods ----- #

    def calculate(self, variable_name, period, **parameters):
        """
            Calculate the variable ``variable_name`` for the period ``period``, using the variable formula if it exists.

            :returns: A numpy array containing the result of the calculation
        """
        entity = self.get_variable_entity(variable_name)
        holder = entity.get_holder(variable_name)
        variable = self.tax_benefit_system.get_variable(variable_name)

        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)

        if self.trace:
            self.tracer.record_calculation_start(variable.name, period, **parameters)

        self._check_period_consistency(period, variable)

        # First look for a value already cached
        cached_array = holder.get_array(period)
        if cached_array is not None:
            if self.trace:
                self.tracer.record_calculation_end(variable.name, period, cached_array, **parameters)
            return cached_array

        array = None

        # First, try to run a formula
        try:
            self._check_for_cycle(variable, period)
            array = self._run_formula(variable, entity, period)

            # If no result, use the default value and cache it
            if array is None:
                array = holder.default_array()

            array = self._cast_formula_result(array, variable)

            holder.put_in_cache(array, period)
        except SpiralError:
            array = holder.default_array()
        finally:
            if self.trace:
                self.tracer.record_calculation_end(variable.name, period, array, **parameters)
            self._clean_cycle_detection_data(variable.name)

        self.purge_cache_of_invalid_values()

        return array

    def purge_cache_of_invalid_values(self):
        # We wait for the end of calculate(), signalled by an empty stack, before purging the cache
        if self.computation_stack:
            return
        for (_name, _period) in self.invalidated_caches:
            holder = self.get_holder(_name)
            holder.delete_arrays(_period)

    def calculate_add(self, variable_name, period, **parameters):
        variable = self.tax_benefit_system.get_variable(variable_name)

        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)

        # Check that the requested period matches definition_period
        if periods.unit_weight(variable.definition_period) > periods.unit_weight(period.unit):
            raise ValueError("Unable to compute variable '{0}' for period {1}: '{0}' can only be computed for {2}-long periods. You can use the DIVIDE option to get an estimate of {0} by dividing the yearly value by 12, or change the requested period to 'period.this_year'.".format(
                variable.name,
                period,
                variable.definition_period
                ).encode('utf-8'))

        if variable.definition_period not in [periods.DAY, periods.MONTH, periods.YEAR]:
            raise ValueError("Unable to sum constant variable '{}' over period {}: only variables defined daily, monthly, or yearly can be summed over time.".format(
                variable.name,
                period).encode('utf-8'))

        return sum(
            self.calculate(variable_name, sub_period, **parameters)
            for sub_period in period.get_subperiods(variable.definition_period)
            )

    def calculate_divide(self, variable_name, period, **parameters):
        variable = self.tax_benefit_system.get_variable(variable_name)

        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)

        # Check that the requested period matches definition_period
        if variable.definition_period != periods.YEAR:
            raise ValueError("Unable to divide the value of '{}' over time on period {}: only variables defined yearly can be divided over time.".format(
                variable_name,
                period).encode('utf-8'))

        if period.size != 1:
            raise ValueError("DIVIDE option can only be used for a one-year or a one-month requested period")

        if period.unit == periods.MONTH:
            computation_period = period.this_year
            return self.calculate(variable_name, period = computation_period, **parameters) / 12.
        elif period.unit == periods.YEAR:
            return self.calculate(variable_name, period, **parameters)

        raise ValueError("Unable to divide the value of '{}' to match period {}.".format(
            variable_name,
            period).encode('utf-8'))

    def calculate_output(self, variable_name, period):
        """
            Calculate the value of a variable using the ``calculate_output`` attribute of the variable.
        """

        variable = self.tax_benefit_system.get_variable(variable_name, check_existence = True)

        if variable.calculate_output is None:
            return self.calculate(variable_name, period)

        return variable.calculate_output(self, variable_name, period)

    def trace_parameters_at_instant(self, formula_period):
        return TracingParameterNodeAtInstant(
            self.tax_benefit_system.get_parameters_at_instant(formula_period),
            self.tracer
            )

    def _run_formula(self, variable, entity, period):
        """
            Find the ``variable`` formula for the given ``period`` if it exists, and apply it to ``entity``.
        """

        formula = variable.get_formula(period)
        if formula is None:
            return None

        if self.trace:
            parameters_at = self.trace_parameters_at_instant
        else:
            parameters_at = self.tax_benefit_system.get_parameters_at_instant

        if formula.__code__.co_argcount == 2:
            array = formula(entity, period)
        else:
            array = formula(entity, period, parameters_at)

        self._check_formula_result(array, variable, entity, period)
        return array

    def _check_period_consistency(self, period, variable):
        """
            Check that a period matches the variable definition_period
        """
        if variable.definition_period == periods.ETERNITY:
            return  # For variables which values are constant in time, all periods are accepted

        if variable.definition_period == periods.MONTH and period.unit != periods.MONTH:
            raise ValueError("Unable to compute variable '{0}' for period {1}: '{0}' must be computed for a whole month. You can use the ADD option to sum '{0}' over the requested period, or change the requested period to 'period.first_month'.".format(
                variable.name,
                period
                ).encode('utf-8'))

        if variable.definition_period == periods.YEAR and period.unit != periods.YEAR:
            raise ValueError("Unable to compute variable '{0}' for period {1}: '{0}' must be computed for a whole year. You can use the DIVIDE option to get an estimate of {0} by dividing the yearly value by 12, or change the requested period to 'period.this_year'.".format(
                variable.name,
                period
                ).encode('utf-8'))

        if period.size != 1:
            raise ValueError("Unable to compute variable '{0}' for period {1}: '{0}' must be computed for a whole {2}. You can use the ADD option to sum '{0}' over the requested period.".format(
                variable.name,
                period,
                'month' if variable.definition_period == periods.MONTH else 'year'
                ).encode('utf-8'))

    def _check_formula_result(self, value, variable, entity, period):

        assert isinstance(value, np.ndarray), (linesep.join([
            "You tried to compute the formula '{0}' for the period '{1}'.".format(variable.name, str(period)),
            "The formula '{0}@{1}' should return a Numpy array;".format(variable.name, str(period)),
            "instead it returned '{0}' of {1}.".format(value, type(value)),
            "Learn more about Numpy arrays and vectorial computing:",
            "<https://openfisca.org/doc/coding-the-legislation/25_vectorial_computing.html.>"
            ]))

        assert value.size == entity.count, \
            "Function {}@{}<{}>() --> <{}>{} returns an array of size {}, but size {} is expected for {}".format(
                variable.name, entity.key, str(period), str(period), stringify_array(value),
                value.size, entity.count, entity.key).encode('utf-8')

        if self.debug:
            try:
                # cf https://stackoverflow.com/questions/6736590/fast-check-for-nan-in-numpy
                if np.isnan(np.min(value)):
                    nan_count = np.count_nonzero(np.isnan(value))
                    raise NaNCreationError("Function {}@{}<{}>() --> <{}>{} returns {} NaN value(s)".format(
                        variable.name, entity.key, str(period), str(period), stringify_array(value),
                        nan_count).encode('utf-8'))
            except TypeError:
                pass

    def _cast_formula_result(self, value, variable):
        if variable.value_type == Enum and not isinstance(value, EnumArray):
            return variable.possible_values.encode(value)

        if value.dtype != variable.dtype:
            return value.astype(variable.dtype)

        return value

    # ----- Handle circular dependencies in a calculation ----- #

    def _check_for_cycle(self, variable, period):
        """
        Raise an exception in the case of a circular definition, where evaluating a variable for
        a given period loops around to evaluating the same variable/period pair. Also guards, as
        a heuristic, against "quasicircles", where the evaluation of a variable at a period involves
        the same variable at a different period.
        """
        previous_periods = [_period for (_name, _period) in self.computation_stack if _name == variable.name]
        self.computation_stack.append((variable.name, str(period)))
        if str(period) in previous_periods:
            raise CycleError("Circular definition detected on formula {}@{}".format(variable.name, period))
        spiral = len(previous_periods) >= self.max_spiral_loops
        if spiral:
            self.invalidate_spiral_variables(variable)
            message = "Quasicircular definition detected on formula {}@{} involving {}".format(variable.name, period, self.computation_stack)
            raise SpiralError(message, variable.name)

    def invalidate_spiral_variables(self, variable):
        # Visit the stack, from the bottom (most recent) up; we know that we'll find
        # the variable implicated in the spiral (max_spiral_loops+1) times; we keep the
        # intermediate values computed (to avoid impacting performance) but we mark them
        # for deletion from the cache once the calculation ends.
        count = 0
        for frame in reversed(self.computation_stack):
            self.invalidated_caches.add(frame)
            if frame[0] == variable.name:
                count += 1
                if count > self.max_spiral_loops:
                    break

    def _clean_cycle_detection_data(self, variable_name):
        """
        When the value of a formula have been computed, remove the period from
        requested_periods_by_variable_name[variable_name] and delete the latter if empty.
        """
        self.computation_stack.pop()

    # ----- Methods to access stored values ----- #

    def get_array(self, variable_name, period):
        """
            Return the value of ``variable_name`` for ``period``, if this value is alreay in the cache (if it has been set as an input or previously calculated).

            Unlike :any:`calculate`, this method *does not* trigger calculations and *does not* use any formula.
        """
        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)
        return self.get_holder(variable_name).get_array(period)

    def get_holder(self, variable_name):
        """
            Get the :any:`Holder` associated with the variable ``variable_name`` for the simulation
        """
        return self.get_variable_entity(variable_name).get_holder(variable_name)

    def get_memory_usage(self, variables = None):
        """
            Get data about the virtual memory usage of the simulation
        """
        result = dict(
            total_nb_bytes = 0,
            by_variable = {}
            )
        for entity in self.entities.values():
            entity_memory_usage = entity.get_memory_usage(variables = variables)
            result['total_nb_bytes'] += entity_memory_usage['total_nb_bytes']
            result['by_variable'].update(entity_memory_usage['by_variable'])
        return result

    # ----- Misc ----- #

    def delete_arrays(self, variable, period = None):
        """
            Delete a variable's value for a given period

            :param variable: the variable to be set
            :param period: the period for which the value should be deleted

            Example:

            >>> from openfisca_country_template import CountryTaxBenefitSystem
            >>> simulation = Simulation(CountryTaxBenefitSystem())
            >>> simulation.set_input('age', '2018-04', [12, 14])
            >>> simulation.set_input('age', '2018-05', [13, 14])
            >>> simulation.get_array('age', '2018-05')
            array([13, 14], dtype=int32)
            >>> simulation.delete_arrays('age', '2018-05')
            >>> simulation.get_array('age', '2018-04')
            array([12, 14], dtype=int32)
            >>> simulation.get_array('age', '2018-05') is None
            True
            >>> simulation.set_input('age', '2018-05', [13, 14])
            >>> simulation.delete_arrays('age')
            >>> simulation.get_array('age', '2018-04') is None
            True
            >>> simulation.get_array('age', '2018-05') is None
            True
        """
        self.get_holder(variable).delete_arrays(period)

    def get_known_periods(self, variable):
        """
            Get a list variable's known period, i.e. the periods where a value has been initialized and

            :param variable: the variable to be set

            Example:

            >>> from openfisca_country_template import CountryTaxBenefitSystem
            >>> simulation = Simulation(CountryTaxBenefitSystem())
            >>> simulation.set_input('age', '2018-04', [12, 14])
            >>> simulation.set_input('age', '2018-05', [13, 14])
            >>> simulation.get_known_periods('age')
            [Period((u'month', Instant((2018, 5, 1)), 1)), Period((u'month', Instant((2018, 4, 1)), 1))]

        """
        return self.get_holder(variable).get_known_periods()

    def set_input(self, variable_name, period, value):
        """
            Set a variable's value for a given period

            :param variable: the variable to be set
            :param value: the input value for the variable
            :param period: the period for which the value is setted

            Example:
            >>> from openfisca_country_template import CountryTaxBenefitSystem
            >>> simulation = Simulation(CountryTaxBenefitSystem())
            >>> simulation.set_input('age', '2018-04', [12, 14])
            >>> simulation.get_array('age', '2018-04')
            array([12, 14], dtype=int32)

            If a ``set_input`` property has been set for the variable, this method may accept inputs for periods not matching the ``definition_period`` of the variable. To read more about this, check the `documentation <https://openfisca.org/doc/coding-the-legislation/35_periods.html#automatically-process-variable-inputs-defined-for-periods-not-matching-the-definitionperiod>`_.
        """
        variable = self.tax_benefit_system.get_variable(variable_name)
        period = periods.period(period)
        if ((variable.end is not None) and (period.start.date > variable.end)):
            return
        self.get_holder(variable_name).set_input(period, value)

    def get_variable_entity(self, variable_name):
        variable = self.tax_benefit_system.get_variable(variable_name, check_existence = True)
        return self.get_entity(variable.entity)

    def get_entity(self, entity_type = None, plural = None):
        if entity_type:
            return self.entities[entity_type.key]
        if plural:
            return next((entity for entity in self.entities.values() if entity.plural == plural), None)

    def clone(self, debug = False, trace = False):
        """
            Copy the simulation just enough to be able to run the copy without modifying the original simulation
        """
        new = empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.items():
            if key not in ('debug', 'trace', 'tracer'):
                new_dict[key] = value

        new.persons = self.persons.clone(new)
        setattr(new, new.persons.key, new.persons)
        new.entities = {new.persons.key: new.persons}

        for entity_class in self.tax_benefit_system.group_entities:
            entity = self.entities[entity_class.key].clone(new)
            new.entities[entity.key] = entity
            setattr(new, entity_class.key, entity)  # create shortcut simulation.household (for instance)

        new.debug = debug
        new.trace = trace

        return new


def calculate_output_add(simulation, variable_name, period):
    return simulation.calculate_add(variable_name, period)


def calculate_output_divide(simulation, variable_name, period):
    return simulation.calculate_divide(variable_name, period)
