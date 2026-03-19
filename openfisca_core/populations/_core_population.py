from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

import traceback

import numpy

from openfisca_core import holders, periods

from . import types as t
from ._errors import (
    IncompatibleOptionsError,
    InvalidArraySizeError,
    InvalidOptionError,
    PeriodValidityError,
)

#: Type variable for a covariant data type.
_DT_co = TypeVar("_DT_co", covariant=True, bound=t.VarDType)


class CorePopulation:
    """Base class to build populations from.

    Args:
        entity: The :class:`~entities.CoreEntity` of the population.
        *__args: Variable length argument list.
        **__kwds: Arbitrary keyword arguments.

    """

    #: The number :class:`~entities.CoreEntity` members in the population.
    count: int = 0

    #: The :class:`~entities.CoreEntity` of the population.
    entity: t.CoreEntity

    #: A pseudo index for the members of the population.
    ids: Sequence[str] = []

    #: The :class:`~simulations.Simulation` for which the population is calculated.
    simulation: None | t.Simulation = None

    def __init__(self, entity: t.CoreEntity, *__args: object, **__kwds: object) -> None:
        self.entity = entity
        self._holders: t.HolderByVariable = {}

    def __call__(
        self,
        variable_name: t.VariableName,
        period: t.PeriodLike,
        options: None | Sequence[t.Option] = None,
    ) -> None | t.VarArray:
        """Calculate ``variable_name`` for ``period``, using the formula if it exists.

        Args:
            variable_name: The name of the variable to calculate.
            period: The period to calculate the variable for.
            options: The options to use for the calculation.

        Returns:
            None: If there is no :class:`~simulations.Simulation`.
            ndarray[generic]: The result of the calculation.

        Raises:
            IncompatibleOptionsError: If the options are incompatible.
            InvalidOptionError: If the option is invalid.

        Examples:
            >>> from openfisca_core import (
            ...     entities,
            ...     periods,
            ...     populations,
            ...     simulations,
            ...     taxbenefitsystems,
            ...     variables,
            ... )

            >>> class Person(entities.SingleEntity): ...

            >>> person = Person("person", "people", "", "")
            >>> period = periods.Period.eternity()
            >>> population = populations.CorePopulation(person)
            >>> population.count = 3
            >>> population("salary", period)

            >>> tbs = taxbenefitsystems.TaxBenefitSystem([person])
            >>> person.set_tax_benefit_system(tbs)
            >>> simulation = simulations.Simulation(tbs, {person.key: population})
            >>> population("salary", period)
            Traceback (most recent call last):
            VariableNotFoundError: You tried to calculate or to set a value ...

            >>> class Salary(variables.Variable):
            ...     definition_period = periods.ETERNITY
            ...     entity = person
            ...     value_type = int

            >>> tbs.add_variable(Salary)
            <openfisca_core.populations._core_population.Salary object at...

            >>> population(Salary().name, period)
            array([0, 0, 0], dtype=int32)

            >>> class Tax(Salary):
            ...     default_value = 100.0
            ...     definition_period = periods.ETERNITY
            ...     entity = person
            ...     value_type = float

            >>> tbs.add_variable(Tax)
            <openfisca_core.populations._core_population.Tax object at...

            >>> population(Tax().name, period)
            array([100., 100., 100.], dtype=float32)

            >>> population(Tax().name, period, [populations.ADD])
            Traceback (most recent call last):
            ValueError: Unable to ADD constant variable 'Tax' over the perio...

            >>> population(Tax().name, period, [populations.DIVIDE])
            Traceback (most recent call last):
            ValueError: Unable to DIVIDE constant variable 'Tax' over the pe...

            >>> population(Tax().name, period, [populations.ADD, populations.DIVIDE])
            Traceback (most recent call last):
            IncompatibleOptionsError: Options ADD and DIVIDE are incompatibl...

            >>> population(Tax().name, period, ["LAGRANGIAN"])
            Traceback (most recent call last):
            InvalidOptionError: Option LAGRANGIAN is not a valid option (try...

        """
        if self.simulation is None:
            return None

        calculate = t.Calculate(
            variable=variable_name,
            period=periods.period(period),
            option=options,
        )

        self.entity.check_variable_defined_for_entity(calculate.variable)
        self.check_period_validity(calculate.variable, calculate.period)

        if not isinstance(calculate.option, Sequence):
            return self.simulation.calculate(
                calculate.variable,
                calculate.period,
            )

        if t.Option.ADD in calculate.option and t.Option.DIVIDE in calculate.option:
            raise IncompatibleOptionsError(variable_name)

        if t.Option.ADD in calculate.option:
            return self.simulation.calculate_add(
                calculate.variable,
                calculate.period,
            )

        if t.Option.DIVIDE in calculate.option:
            return self.simulation.calculate_divide(
                calculate.variable,
                calculate.period,
            )

        raise InvalidOptionError(calculate.option[0], variable_name)

    def empty_array(self) -> t.FloatArray:
        """Return an empty array.

        Returns:
            ndarray[float32]: An empty array.

        Examples:
            >>> import numpy

            >>> from openfisca_core import populations as p

            >>> class Population(p.CorePopulation): ...

            >>> population = Population(None)
            >>> population.empty_array()
            array([], dtype=float32)

            >>> population.count = 3
            >>> population.empty_array()
            array([0., 0., 0.], dtype=float32)

        """
        return numpy.zeros(self.count, dtype=t.FloatDType)

    def filled_array(
        self, value: _DT_co, dtype: None | t.DTypeLike = None
    ) -> t.Array[_DT_co]:
        """Return an array filled with a value.

        Args:
            value: The value to fill the array with.
            dtype: The data type of the array.

        Returns:
            ndarray[generic]: An array filled with the value.

        Examples:
            >>> import numpy

            >>> from openfisca_core import populations

            >>> class Population(populations.CorePopulation): ...

            >>> population = Population(None)
            >>> population.count = 3
            >>> population.filled_array(1)
            array([1, 1, 1])

            >>> population.filled_array(numpy.float32(1))
            array([1., 1., 1.], dtype=float32)

            >>> population.filled_array(1, dtype=str)
            array(['1', '1', '1'], dtype='<U1')

            >>> population.filled_array("hola", dtype=numpy.uint8)
            Traceback (most recent call last):
            ValueError: could not convert string to float: 'hola'

        """
        return numpy.full(self.count, value, dtype)

    def get_index(self, id: str) -> int:
        """Return the index of an `id``.

        Args:
            id: The id to get the index for.

        Returns:
            int: The index of the id.

        Examples:
            >>> from openfisca_core import entities, populations

            >>> class Person(entities.SingleEntity): ...

            >>> person = Person("person", "people", "", "")
            >>> population = populations.CorePopulation(person)
            >>> population.ids = ["Juan", "Megan", "Brahim"]

            >>> population.get_index("Megan")
            1

            >>> population.get_index("Ibrahim")
            Traceback (most recent call last):
            ValueError: 'Ibrahim' is not in list

        """
        return self.ids.index(id)

    # Calculations

    def check_array_compatible_with_entity(self, array: t.VarArray) -> None:
        """Check if an array is compatible with the population.

        Args:
            array: The array to check.

        Raises:
            InvalidArraySizeError: If the array is not compatible.

        Examples:
            >>> import numpy

            >>> from openfisca_core import entities, populations

            >>> class Person(entities.SingleEntity): ...

            >>> person = Person("person", "people", "", "")
            >>> population = populations.CorePopulation(person)
            >>> population.count = 3

            >>> array = numpy.array([1, 2, 3])
            >>> population.check_array_compatible_with_entity(array)

            >>> array = numpy.array([1, 2, 3, 4])
            >>> population.check_array_compatible_with_entity(array)
            Traceback (most recent call last):
            InvalidArraySizeError: Input [1 2 3 4] is not a valid value for t...

        """
        if self.count == array.size:
            return
        raise InvalidArraySizeError(array, self.entity.key, self.count)

    @staticmethod
    def check_period_validity(
        variable_name: t.VariableName,
        period: None | t.PeriodLike = None,
    ) -> None:
        """Check if a period is valid.

        Args:
            variable_name: The name of the variable.
            period: The period to check.

        Raises:
            PeriodValidityError: If the period is not valid.

        Examples:
            >>> from openfisca_core import entities, periods, populations

            >>> class Person(entities.SingleEntity): ...

            >>> person = Person("person", "people", "", "")
            >>> period = periods.Period("2017-04")
            >>> population = populations.CorePopulation(person)

            >>> population.check_period_validity("salary")
            Traceback (most recent call last):
            PeriodValidityError: You requested computation of variable "sala...

            >>> population.check_period_validity("salary", 2017)

            >>> population.check_period_validity("salary", "2017-04")

            >>> population.check_period_validity("salary", period)

        """
        if isinstance(period, (int, str, periods.Period)):
            return
        stack = traceback.extract_stack()
        filename, line_number, _, line_of_code = stack[-3]
        raise PeriodValidityError(variable_name, filename, line_number, line_of_code)

    # Helpers

    def get_holder(self, variable_name: t.VariableName) -> t.Holder:
        """Return the holder of a variable.

        Args:
            variable_name: The name of the variable.

        Returns:
            Holder: The holder of the variable.

        Examples:
            >>> from openfisca_core import (
            ...     entities,
            ...     holders,
            ...     periods,
            ...     populations,
            ...     simulations,
            ...     taxbenefitsystems,
            ...     simulations,
            ...     variables,
            ... )

            >>> class Person(entities.SingleEntity): ...

            >>> person = Person("person", "people", "", "")

            >>> class Salary(variables.Variable):
            ...     definition_period = periods.WEEK
            ...     entity = person
            ...     value_type = int

            >>> tbs = taxbenefitsystems.TaxBenefitSystem([person])
            >>> person.set_tax_benefit_system(tbs)
            >>> population = populations.SinglePopulation(person)
            >>> simulation = simulations.Simulation(tbs, {person.key: population})
            >>> population.get_holder("income_tax")
            Traceback (most recent call last):
            VariableNotFoundError: You tried to calculate or to set a value ...

            >>> tbs.add_variable(Salary)
            <openfisca_core.populations._core_population.Salary object at...

            >>> salary = Salary()
            >>> population.get_holder(salary.name)
            <openfisca_core.holders.holder.Holder object at ...

        """
        self.entity.check_variable_defined_for_entity(variable_name)
        holder = self._holders.get(variable_name)
        if holder:
            return holder
        variable = self.entity.get_variable(variable_name)
        self._holders[variable_name] = holder = holders.Holder(variable, self)
        return holder

    def get_memory_usage(
        self,
        variables: None | Sequence[t.VariableName] = None,
    ) -> t.MemoryUsageByVariable:
        """Return the memory usage of the population per variable.

        Args:
            variables: The variables to get the memory usage for.

        Returns:
            MemoryUsageByVariable: The memory usage of the population per variable.

        Examples:
            >>> from openfisca_core import (
            ...     entities,
            ...     holders,
            ...     periods,
            ...     populations,
            ...     simulations,
            ...     taxbenefitsystems,
            ...     simulations,
            ...     variables,
            ... )

            >>> class Person(entities.SingleEntity): ...

            >>> person = Person("person", "people", "", "")

            >>> class Salary(variables.Variable):
            ...     definition_period = periods.WEEK
            ...     entity = person
            ...     value_type = int

            >>> tbs = taxbenefitsystems.TaxBenefitSystem([person])
            >>> population = populations.SinglePopulation(person)
            >>> simulation = simulations.Simulation(tbs, {person.key: population})
            >>> salary = Salary()
            >>> holder = holders.Holder(salary, population)
            >>> population._holders[salary.name] = holder

            >>> population.get_memory_usage()
            {'total_nb_bytes': 0, 'by_variable': {'Salary': {'nb_cells_by...}}}

            >>> population.get_memory_usage([salary.name])
            {'total_nb_bytes': 0, 'by_variable': {'Salary': {'nb_cells_by...}}}

        """
        holders_memory_usage = {
            variable_name: holder.get_memory_usage()
            for variable_name, holder in self._holders.items()
            if variables is None or variable_name in variables
        }

        total_memory_usage = sum(
            holder_memory_usage["total_nb_bytes"]
            for holder_memory_usage in holders_memory_usage.values()
        )

        return t.MemoryUsageByVariable(
            total_nb_bytes=total_memory_usage,
            by_variable=holders_memory_usage,
        )


__all__ = ["CorePopulation"]
