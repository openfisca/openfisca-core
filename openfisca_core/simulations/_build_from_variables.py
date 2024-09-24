"""This module contains the _BuildFromVariables class."""

from __future__ import annotations

from typing_extensions import Self

from openfisca_core import errors

from ._build_default_simulation import _BuildDefaultSimulation
from ._type_guards import is_variable_dated
from .simulation import Simulation
from .typing import Entity, Population, TaxBenefitSystem, Variables


class _BuildFromVariables:
    """Build a simulation from variables.

    Args:
        tax_benefit_system(TaxBenefitSystem): The tax-benefit system.
        params(Variables): The simulation parameters.

    Examples:
        >>> from openfisca_core import entities, periods, taxbenefitsystems, variables

        >>> role = {"key": "stray", "plural": "stray", "label": "", "doc": ""}
        >>> single_entity = entities.Entity("dog", "dogs", "", "")
        >>> group_entity = entities.GroupEntity("pack", "packs", "", "", [role])

        >>> class salary(variables.Variable):
        ...     definition_period = periods.DateUnit.MONTH
        ...     entity = single_entity
        ...     value_type = int

        >>> class taxes(variables.Variable):
        ...     definition_period = periods.DateUnit.MONTH
        ...     entity = group_entity
        ...     value_type = int

        >>> test_entities = [single_entity, group_entity]
        >>> tax_benefit_system = taxbenefitsystems.TaxBenefitSystem(test_entities)
        >>> tax_benefit_system.load_variable(salary)
        <...salary object at ...>
        >>> tax_benefit_system.load_variable(taxes)
        <...taxes object at ...>
        >>> period = "2023-12"
        >>> variables = {"salary": {period: 10000}, "taxes": 5000}
        >>> builder = (
        ...     _BuildFromVariables(tax_benefit_system, variables, period)
        ...     .add_dated_values()
        ...     .add_undated_values()
        ... )

        >>> dogs = builder.populations["dog"].get_holder("salary")
        >>> dogs.get_array(period)
        array([10000], dtype=int32)

        >>> pack = builder.populations["pack"].get_holder("taxes")
        >>> pack.get_array(period)
        array([5000], dtype=int32)

    """

    #: The number of Population.
    count: int

    #: The Simulation's default period.
    default_period: str | None

    #: The built populations.
    populations: dict[str, Population[Entity]]

    #: The built simulation.
    simulation: Simulation

    #: The simulation parameters.
    variables: Variables

    def __init__(
        self,
        tax_benefit_system: TaxBenefitSystem,
        params: Variables,
        default_period: str | None = None,
    ) -> None:
        self.count = _person_count(params)

        default_builder = (
            _BuildDefaultSimulation(tax_benefit_system, self.count)
            .add_count()
            .add_ids()
            .add_members_entity_id()
        )

        self.variables = params
        self.simulation = default_builder.simulation
        self.populations = default_builder.populations
        self.default_period = default_period

    def add_dated_values(self) -> Self:
        """Add the dated input values to the Simulation.

        Returns:
            _BuildFromVariables: The builder.

        Examples:
            >>> from openfisca_core import entities, periods, taxbenefitsystems, variables

            >>> role = {"key": "stray", "plural": "stray", "label": "", "doc": ""}
            >>> single_entity = entities.Entity("dog", "dogs", "", "")
            >>> group_entity = entities.GroupEntity("pack", "packs", "", "", [role])


            >>> class salary(variables.Variable):
            ...     definition_period = periods.DateUnit.MONTH
            ...     entity = single_entity
            ...     value_type = int

            >>> class taxes(variables.Variable):
            ...     definition_period = periods.DateUnit.MONTH
            ...     entity = group_entity
            ...     value_type = int

            >>> test_entities = [single_entity, group_entity]
            >>> tax_benefit_system = taxbenefitsystems.TaxBenefitSystem(test_entities)
            >>> tax_benefit_system.load_variable(salary)
            <...salary object at ...>
            >>> tax_benefit_system.load_variable(taxes)
            <...taxes object at ...>
            >>> period = "2023-12"
            >>> variables = {"salary": {period: 10000}, "taxes": 5000}
            >>> builder = _BuildFromVariables(tax_benefit_system, variables)
            >>> builder.add_dated_values()
            <..._BuildFromVariables object at ...>

            >>> dogs = builder.populations["dog"].get_holder("salary")
            >>> dogs.get_array(period)
            array([10000], dtype=int32)

            >>> pack = builder.populations["pack"].get_holder("taxes")
            >>> pack.get_array(period)

        """
        for variable, value in self.variables.items():
            if is_variable_dated(dated_variable := value):
                for period, dated_value in dated_variable.items():
                    self.simulation.set_input(variable, period, dated_value)

        return self

    def add_undated_values(self) -> Self:
        """Add the undated input values to the Simulation.

        Returns:
            _BuildFromVariables: The builder.

        Raises:
            SituationParsingError: If there is not a default period set.

        Examples:
            >>> from openfisca_core import entities, periods, taxbenefitsystems, variables

            >>> role = {"key": "stray", "plural": "stray", "label": "", "doc": ""}
            >>> single_entity = entities.Entity("dog", "dogs", "", "")
            >>> group_entity = entities.GroupEntity("pack", "packs", "", "", [role])

            >>> class salary(variables.Variable):
            ...     definition_period = periods.DateUnit.MONTH
            ...     entity = single_entity
            ...     value_type = int

            >>> class taxes(variables.Variable):
            ...     definition_period = periods.DateUnit.MONTH
            ...     entity = group_entity
            ...     value_type = int

            >>> test_entities = [single_entity, group_entity]
            >>> tax_benefit_system = taxbenefitsystems.TaxBenefitSystem(test_entities)
            >>> tax_benefit_system.load_variable(salary)
            <...salary object at ...>
            >>> tax_benefit_system.load_variable(taxes)
            <...taxes object at ...>
            >>> period = "2023-12"
            >>> variables = {"salary": {period: 10000}, "taxes": 5000}
            >>> builder = _BuildFromVariables(tax_benefit_system, variables)
            >>> builder.add_undated_values()
            Traceback (most recent call last):
            openfisca_core.errors.situation_parsing_error.SituationParsingError
            >>> builder.default_period = period
            >>> builder.add_undated_values()
            <..._BuildFromVariables object at ...>

            >>> dogs = builder.populations["dog"].get_holder("salary")
            >>> dogs.get_array(period)

            >>> pack = builder.populations["pack"].get_holder("taxes")
            >>> pack.get_array(period)
            array([5000], dtype=int32)

        """
        for variable, value in self.variables.items():
            if not is_variable_dated(undated_value := value):
                if (period := self.default_period) is None:
                    message = (
                        "Can't deal with type: expected object. Input "
                        "variables should be set for specific periods. For "
                        "instance: "
                        "    {'salary': {'2017-01': 2000, '2017-02': 2500}}"
                        "    {'birth_date': {'ETERNITY': '1980-01-01'}}"
                    )

                    raise errors.SituationParsingError([variable], message)

                self.simulation.set_input(variable, period, undated_value)

        return self


def _person_count(params: Variables) -> int:
    try:
        first_value = next(iter(params.values()))

        if isinstance(first_value, dict):
            first_value = next(iter(first_value.values()))

        if isinstance(first_value, str):
            return 1

        return len(first_value)

    except Exception:
        return 1
