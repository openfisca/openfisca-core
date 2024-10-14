from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

import traceback

import numpy

from openfisca_core import holders, periods

from . import types as t
from ._errors import InvalidArraySizeError

#: Type variable for a covariant data type.
_DT_co = TypeVar("_DT_co", covariant=True, bound=t.VarDType)


class CorePopulation:
    """Base class to build populations from.

    Args:
        entity: The :class:`.CoreEntity` of the population.
        *__args: Variable length argument list.
        **__kwds: Arbitrary keyword arguments.

    """

    #: ???
    count: int = 0

    #: The :class:`.CoreEntity` of the population.
    entity: t.CoreEntity

    #: ???
    ids: Sequence[str] = []

    #: ???
    simulation: None | t.Simulation = None

    def __init__(self, entity: t.CoreEntity, *__args: object, **__kwds: object) -> None:
        self.entity = entity
        self._holders: t.HolderByVariable = {}

    def __call__(
        self,
        variable_name: t.VariableName,
        period: None | t.PeriodLike = None,
        options: None | Sequence[t.Option] = None,
    ) -> None | t.FloatArray:
        """Calculate ``variable_name`` for ``period``, using the formula if it exists.

        # Example:
        # >>> person("salary", "2017-04")
        # >>> array([300.0])

        Returns:
            None: If there is no :class:`.Simulation`.
            ndarray[float32]: The result of the calculation.

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

        if t.Option.ADD in map(str.upper, calculate.option):
            return self.simulation.calculate_add(
                calculate.variable,
                calculate.period,
            )

        if t.Option.DIVIDE in map(str.upper, calculate.option):
            return self.simulation.calculate_divide(
                calculate.variable,
                calculate.period,
            )

        raise ValueError(
            f"Options config.ADD and config.DIVIDE are incompatible (trying to compute variable {variable_name})".encode(),
        )

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

            >>> from openfisca_core import populations as p

            >>> class Population(p.CorePopulation): ...

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
        return self.ids.index(id)

    # Calculations

    def check_array_compatible_with_entity(self, array: t.FloatArray) -> None:
        if self.count == array.size:
            return
        raise InvalidArraySizeError(array, self.entity.key, self.count)

    def check_period_validity(
        self,
        variable_name: str,
        period: None | t.PeriodLike,
    ) -> None:
        if isinstance(period, (int, str, periods.Period)):
            return

        stack = traceback.extract_stack()
        filename, line_number, function_name, line_of_code = stack[-3]
        msg = f"""
You requested computation of variable "{variable_name}", but you did not specify on which period in "{filename}:{line_number}":
    {line_of_code}
When you request the computation of a variable within a formula, you must always specify the period as the second parameter. The convention is to call this parameter "period". For example:
    computed_salary = person('salary', period).
See more information at <https://openfisca.org/doc/coding-the-legislation/35_periods.html#periods-in-variable-definition>.
"""
        raise ValueError(
            msg,
        )

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
