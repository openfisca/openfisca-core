from __future__ import annotations

from collections.abc import Mapping
from typing import NamedTuple

from openfisca_core.types import Population, TaxBenefitSystem, Variable

import tempfile
import warnings

import numpy

from openfisca_core import (
    commons,
    errors,
    indexed_enums,
    periods,
    tracers,
    warnings as core_warnings,
)


class Simulation:
    """Represents a simulation, and handles the calculation logic."""

    tax_benefit_system: TaxBenefitSystem
    populations: dict[str, Population]
    invalidated_caches: set[Cache]

    def __init__(
        self,
        tax_benefit_system: TaxBenefitSystem,
        populations: Mapping[str, Population],
    ) -> None:
        """This constructor is reserved for internal use; see :any:`SimulationBuilder`,
        which is the preferred way to obtain a Simulation initialized with a consistent
        set of Entities.
        """
        self.tax_benefit_system = tax_benefit_system
        assert tax_benefit_system is not None

        self.populations = populations
        self.persons = self.populations[tax_benefit_system.person_entity.key]
        self.link_to_entities_instances()
        self.create_shortcuts()

        self.invalidated_caches = set()

        self.debug = False
        self.trace = False
        self.tracer = tracers.SimpleTracer()
        self.opt_out_cache = False

        # controls the spirals detection; check for performance impact if > 1
        self.max_spiral_loops: int = 1
        self.memory_config = None
        self._data_storage_dir = None

    @property
    def trace(self):
        return self._trace

    @trace.setter
    def trace(self, trace) -> None:
        self._trace = trace
        if trace:
            self.tracer = tracers.FullTracer()
        else:
            self.tracer = tracers.SimpleTracer()

    def link_to_entities_instances(self) -> None:
        for entity_instance in self.populations.values():
            entity_instance.simulation = self

    def create_shortcuts(self) -> None:
        for population in self.populations.values():
            # create shortcut simulation.person and simulation.household (for instance)
            setattr(self, population.entity.key, population)

    @property
    def data_storage_dir(self):
        """Temporary folder used to store intermediate calculation data in case the memory is saturated."""
        if self._data_storage_dir is None:
            self._data_storage_dir = tempfile.mkdtemp(prefix="openfisca_")
            message = [
                (
                    f"Intermediate results will be stored on disk in {self._data_storage_dir} in case of memory overflow."
                ),
                "You should remove this directory once you're done with your simulation.",
            ]
            warnings.warn(
                " ".join(message),
                core_warnings.TempfileWarning,
                stacklevel=2,
            )
        return self._data_storage_dir

    # ----- Calculation methods ----- #

    def calculate(self, variable_name: str, period):
        """Calculate ``variable_name`` for ``period``."""
        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)

        self.tracer.record_calculation_start(variable_name, period)

        try:
            result = self._calculate(variable_name, period)
            self.tracer.record_calculation_result(result)
            return result

        finally:
            self.tracer.record_calculation_end()
            self.purge_cache_of_invalid_values()

    def _calculate(self, variable_name: str, period: periods.Period):
        """Calculate the variable ``variable_name`` for the period ``period``, using the variable formula if it exists.

        :returns: A numpy array containing the result of the calculation
        """
        variable: Variable | None

        population = self.get_variable_population(variable_name)
        holder = population.get_holder(variable_name)
        variable = self.tax_benefit_system.get_variable(
            variable_name,
            check_existence=True,
        )

        if variable is None:
            raise errors.VariableNotFoundError(variable_name, self.tax_benefit_system)

        self._check_period_consistency(period, variable)

        # First look for a value already cached
        cached_array = holder.get_array(period)
        if cached_array is not None:
            return cached_array

        array = None

        # First, try to run a formula
        try:
            self._check_for_cycle(variable.name, period)
            array = self._run_formula(variable, population, period)

            # If no result, use the default value and cache it
            if array is None:
                array = holder.default_array()

            array = self._cast_formula_result(array, variable)
            holder.put_in_cache(array, period)

        except errors.SpiralError:
            array = holder.default_array()

        return array

    def purge_cache_of_invalid_values(self) -> None:
        # We wait for the end of calculate(), signalled by an empty stack, before purging the cache
        if self.tracer.stack:
            return
        for _name, _period in self.invalidated_caches:
            holder = self.get_holder(_name)
            holder.delete_arrays(_period)
        self.invalidated_caches = set()

    def calculate_add(self, variable_name: str, period):
        variable: Variable | None

        variable = self.tax_benefit_system.get_variable(
            variable_name,
            check_existence=True,
        )

        if variable is None:
            raise errors.VariableNotFoundError(variable_name, self.tax_benefit_system)

        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)

        # Check that the requested period matches definition_period
        if periods.unit_weight(variable.definition_period) > periods.unit_weight(
            period.unit,
        ):
            msg = (
                f"Unable to compute variable '{variable.name}' for period "
                f"{period}: '{variable.name}' can only be computed for "
                f"{variable.definition_period}-long periods. You can use the "
                f"DIVIDE option to get an estimate of {variable.name}."
            )
            raise ValueError(
                msg,
            )

        if variable.definition_period not in (
            periods.DateUnit.isoformat + periods.DateUnit.isocalendar
        ):
            msg = (
                f"Unable to ADD constant variable '{variable.name}' over "
                f"the period {period}: eternal variables can't be summed "
                "over time."
            )
            raise ValueError(
                msg,
            )

        return sum(
            self.calculate(variable_name, sub_period)
            for sub_period in period.get_subperiods(variable.definition_period)
        )

    def calculate_divide(self, variable_name: str, period):
        variable: Variable | None

        variable = self.tax_benefit_system.get_variable(
            variable_name,
            check_existence=True,
        )

        if variable is None:
            raise errors.VariableNotFoundError(variable_name, self.tax_benefit_system)

        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)

        if (
            periods.unit_weight(variable.definition_period)
            < periods.unit_weight(period.unit)
            or period.size > 1
        ):
            msg = (
                f"Can't calculate variable '{variable.name}' for period "
                f"{period}: '{variable.name}' can only be computed for "
                f"{variable.definition_period}-long periods. You can use the "
                f"ADD option to get an estimate of {variable.name}."
            )
            raise ValueError(
                msg,
            )

        if variable.definition_period not in (
            periods.DateUnit.isoformat + periods.DateUnit.isocalendar
        ):
            msg = (
                f"Unable to DIVIDE constant variable '{variable.name}' over "
                f"the period {period}: eternal variables can't be divided "
                "over time."
            )
            raise ValueError(
                msg,
            )

        if (
            period.unit
            not in (periods.DateUnit.isoformat + periods.DateUnit.isocalendar)
            or period.size != 1
        ):
            msg = (
                f"Unable to DIVIDE constant variable '{variable.name}' over "
                f"the period {period}: eternal variables can't be used "
                "as a denominator to divide a variable over time."
            )
            raise ValueError(
                msg,
            )

        if variable.definition_period == periods.DateUnit.YEAR:
            calculation_period = period.this_year

        elif variable.definition_period == periods.DateUnit.MONTH:
            calculation_period = period.first_month

        elif variable.definition_period == periods.DateUnit.DAY:
            calculation_period = period.first_day

        elif variable.definition_period == periods.DateUnit.WEEK:
            calculation_period = period.first_week

        else:
            calculation_period = period.first_weekday

        if period.unit == periods.DateUnit.YEAR:
            denominator = calculation_period.size_in_years

        elif period.unit == periods.DateUnit.MONTH:
            denominator = calculation_period.size_in_months

        elif period.unit == periods.DateUnit.DAY:
            denominator = calculation_period.size_in_days

        elif period.unit == periods.DateUnit.WEEK:
            denominator = calculation_period.size_in_weeks

        else:
            denominator = calculation_period.size_in_weekdays

        return self.calculate(variable_name, calculation_period) / denominator

    def calculate_output(self, variable_name: str, period):
        """Calculate the value of a variable using the ``calculate_output`` attribute of the variable."""
        variable: Variable | None

        variable = self.tax_benefit_system.get_variable(
            variable_name,
            check_existence=True,
        )

        if variable is None:
            raise errors.VariableNotFoundError(variable_name, self.tax_benefit_system)

        if variable.calculate_output is None:
            return self.calculate(variable_name, period)

        return variable.calculate_output(self, variable_name, period)

    def trace_parameters_at_instant(self, formula_period):
        return tracers.TracingParameterNodeAtInstant(
            self.tax_benefit_system.get_parameters_at_instant(formula_period),
            self.tracer,
        )

    def _run_formula(self, variable, population, period):
        """Find the ``variable`` formula for the given ``period`` if it exists, and apply it to ``population``."""
        formula = variable.get_formula(period)
        if formula is None:
            return None

        if self.trace:
            parameters_at = self.trace_parameters_at_instant
        else:
            parameters_at = self.tax_benefit_system.get_parameters_at_instant

        if formula.__code__.co_argcount == 2:
            array = formula(population, period)
        else:
            array = formula(population, period, parameters_at)

        return array

    def _check_period_consistency(self, period, variable) -> None:
        """Check that a period matches the variable definition_period."""
        if variable.definition_period == periods.DateUnit.ETERNITY:
            return  # For variables which values are constant in time, all periods are accepted

        if (
            variable.definition_period == periods.DateUnit.YEAR
            and period.unit != periods.DateUnit.YEAR
        ):
            msg = f"Unable to compute variable '{variable.name}' for period {period}: '{variable.name}' must be computed for a whole year. You can use the DIVIDE option to get an estimate of {variable.name} by dividing the yearly value by 12, or change the requested period to 'period.this_year'."
            raise ValueError(
                msg,
            )

        if (
            variable.definition_period == periods.DateUnit.MONTH
            and period.unit != periods.DateUnit.MONTH
        ):
            msg = f"Unable to compute variable '{variable.name}' for period {period}: '{variable.name}' must be computed for a whole month. You can use the ADD option to sum '{variable.name}' over the requested period, or change the requested period to 'period.first_month'."
            raise ValueError(
                msg,
            )

        if (
            variable.definition_period == periods.DateUnit.WEEK
            and period.unit != periods.DateUnit.WEEK
        ):
            msg = f"Unable to compute variable '{variable.name}' for period {period}: '{variable.name}' must be computed for a whole week. You can use the ADD option to sum '{variable.name}' over the requested period, or change the requested period to 'period.first_week'."
            raise ValueError(
                msg,
            )

        if period.size != 1:
            msg = f"Unable to compute variable '{variable.name}' for period {period}: '{variable.name}' must be computed for a whole {variable.definition_period}. You can use the ADD option to sum '{variable.name}' over the requested period."
            raise ValueError(
                msg,
            )

    def _cast_formula_result(self, value, variable):
        if variable.value_type == indexed_enums.Enum and not isinstance(
            value,
            indexed_enums.EnumArray,
        ):
            return variable.possible_values.encode(value)

        if not isinstance(value, numpy.ndarray):
            population = self.get_variable_population(variable.name)
            value = population.filled_array(value)

        if value.dtype != variable.dtype:
            return value.astype(variable.dtype)

        return value

    # ----- Handle circular dependencies in a calculation ----- #

    def _check_for_cycle(self, variable: str, period) -> None:
        """Raise an exception in the case of a circular definition, where evaluating a variable for
        a given period loops around to evaluating the same variable/period pair. Also guards, as
        a heuristic, against "quasicircles", where the evaluation of a variable at a period involves
        the same variable at a different period.
        """
        # The last frame is the current calculation, so it should be ignored from cycle detection
        previous_periods = [
            frame["period"]
            for frame in self.tracer.stack[:-1]
            if frame["name"] == variable
        ]
        if period in previous_periods:
            msg = f"Circular definition detected on formula {variable}@{period}"
            raise errors.CycleError(
                msg,
            )
        spiral = len(previous_periods) >= self.max_spiral_loops
        if spiral:
            self.invalidate_spiral_variables(variable)
            message = f"Quasicircular definition detected on formula {variable}@{period} involving {self.tracer.stack}"
            raise errors.SpiralError(message, variable)

    def invalidate_cache_entry(self, variable: str, period) -> None:
        self.invalidated_caches.add(Cache(variable, period))

    def invalidate_spiral_variables(self, variable: str) -> None:
        # Visit the stack, from the bottom (most recent) up; we know that we'll find
        # the variable implicated in the spiral (max_spiral_loops+1) times; we keep the
        # intermediate values computed (to avoid impacting performance) but we mark them
        # for deletion from the cache once the calculation ends.
        count = 0
        for frame in reversed(self.tracer.stack):
            self.invalidate_cache_entry(str(frame["name"]), frame["period"])
            if frame["name"] == variable:
                count += 1
                if count > self.max_spiral_loops:
                    break

    # ----- Methods to access stored values ----- #

    def get_array(self, variable_name: str, period):
        """Return the value of ``variable_name`` for ``period``, if this value is alreay in the cache (if it has been set as an input or previously calculated).

        Unlike :meth:`.calculate`, this method *does not* trigger calculations and *does not* use any formula.
        """
        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)
        return self.get_holder(variable_name).get_array(period)

    def get_holder(self, variable_name: str):
        """Get the holder associated with the variable."""
        return self.get_variable_population(variable_name).get_holder(variable_name)

    def get_memory_usage(self, variables=None):
        """Get data about the virtual memory usage of the simulation."""
        result = {"total_nb_bytes": 0, "by_variable": {}}
        for entity in self.populations.values():
            entity_memory_usage = entity.get_memory_usage(variables=variables)
            result["total_nb_bytes"] += entity_memory_usage["total_nb_bytes"]
            result["by_variable"].update(entity_memory_usage["by_variable"])
        return result

    # ----- Misc ----- #

    def delete_arrays(self, variable, period=None) -> None:
        """Delete a variable's value for a given period.

        :param variable: the variable to be set
        :param period: the period for which the value should be deleted

        Example:
        >>> from openfisca_country_template import CountryTaxBenefitSystem
        >>> simulation = Simulation(CountryTaxBenefitSystem())
        >>> simulation.set_input("age", "2018-04", [12, 14])
        >>> simulation.set_input("age", "2018-05", [13, 14])
        >>> simulation.get_array("age", "2018-05")
        array([13, 14], dtype=int32)
        >>> simulation.delete_arrays("age", "2018-05")
        >>> simulation.get_array("age", "2018-04")
        array([12, 14], dtype=int32)
        >>> simulation.get_array("age", "2018-05") is None
        True
        >>> simulation.set_input("age", "2018-05", [13, 14])
        >>> simulation.delete_arrays("age")
        >>> simulation.get_array("age", "2018-04") is None
        True
        >>> simulation.get_array("age", "2018-05") is None
        True

        """
        self.get_holder(variable).delete_arrays(period)

    def get_known_periods(self, variable):
        """Get a list variable's known period, i.e. the periods where a value has been initialized and.

        :param variable: the variable to be set

        Example:
        >>> from openfisca_country_template import CountryTaxBenefitSystem
        >>> simulation = Simulation(CountryTaxBenefitSystem())
        >>> simulation.set_input("age", "2018-04", [12, 14])
        >>> simulation.set_input("age", "2018-05", [13, 14])
        >>> simulation.get_known_periods("age")
        [Period((u'month', Instant((2018, 5, 1)), 1)), Period((u'month', Instant((2018, 4, 1)), 1))]

        """
        return self.get_holder(variable).get_known_periods()

    def set_input(self, variable_name: str, period, value) -> None:
        """Set a variable's value for a given period.

        :param variable: the variable to be set
        :param value: the input value for the variable
        :param period: the period for which the value is setted

        Example:
        >>> from openfisca_country_template import CountryTaxBenefitSystem
        >>> simulation = Simulation(CountryTaxBenefitSystem())
        >>> simulation.set_input("age", "2018-04", [12, 14])
        >>> simulation.get_array("age", "2018-04")
        array([12, 14], dtype=int32)

        If a ``set_input`` property has been set for the variable, this method may accept inputs for periods not matching the ``definition_period`` of the variable. To read more about this, check the `documentation <https://openfisca.org/doc/coding-the-legislation/35_periods.html#automatically-process-variable-inputs-defined-for-periods-not-matching-the-definitionperiod>`_.

        """
        variable: Variable | None

        variable = self.tax_benefit_system.get_variable(
            variable_name,
            check_existence=True,
        )

        if variable is None:
            raise errors.VariableNotFoundError(variable_name, self.tax_benefit_system)

        period = periods.period(period)
        if (variable.end is not None) and (period.start.date > variable.end):
            return
        self.get_holder(variable_name).set_input(period, value)

    def get_variable_population(self, variable_name: str) -> Population:
        variable: Variable | None

        variable = self.tax_benefit_system.get_variable(
            variable_name,
            check_existence=True,
        )

        if variable is None:
            raise errors.VariableNotFoundError(variable_name, self.tax_benefit_system)

        return self.populations[variable.entity.key]

    def get_population(self, plural: str | None = None) -> Population | None:
        return next(
            (
                population
                for population in self.populations.values()
                if population.entity.plural == plural
            ),
            None,
        )

    def get_entity(
        self,
        plural: str | None = None,
    ) -> Population | None:
        population = self.get_population(plural)
        return population and population.entity

    def describe_entities(self):
        return {
            population.entity.plural: population.ids
            for population in self.populations.values()
        }

    def clone(self, debug=False, trace=False):
        """Copy the simulation just enough to be able to run the copy without modifying the original simulation."""
        new = commons.empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.items():
            if key not in ("debug", "trace", "tracer"):
                new_dict[key] = value

        new.persons = self.persons.clone(new)
        setattr(new, new.persons.entity.key, new.persons)
        new.populations = {new.persons.entity.key: new.persons}

        for entity in self.tax_benefit_system.group_entities:
            population = self.populations[entity.key].clone(new)
            new.populations[entity.key] = population
            setattr(
                new,
                entity.key,
                population,
            )  # create shortcut simulation.household (for instance)

        new.debug = debug
        new.trace = trace

        return new


class Cache(NamedTuple):
    variable: str
    period: periods.Period
