"""Rules for simulations, aka business invariants."""

from typing import TypedDict, Union
from typing_extensions import TypeAlias

from openfisca_core import commons, periods

from .types import Failure, Period, Success, Variable

#: Type alias for an either monad.
Either: TypeAlias = Union[Failure[str], Success["_State"]]


class _State(TypedDict):
    """State of the rule-checking."""

    #: The variable to check.
    variable: Variable

    #: The period to check.
    period: Period


def _check_periods_compatibility_1(state: _State) -> Either:
    """When definition period is month/day and period is week.

    Examples:
        >>> from openfisca_core import entities, periods, variables

        >>> entity = entities.SingleEntity("", "", "", "")

        >>> class Variable(variables.Variable):
        ...    definition_period = periods.WEEK
        ...    entity = entity
        ...    value_type = int

        >>> variable = Variable()
        >>> period = periods.period("2020-W01")
        >>> state = {"variable": variable, "period": period}

        >>> _check_periods_compatibility_1(state)
        Success(_value={'variable': ..., 'period': ...})

        >>> variable.definition_period = periods.MONTH
        >>> _check_periods_compatibility_1(state)
        Failure(_value="Unable to compute variable 'Variable' for period 2...")

    Args:
        state(_State): The state of the rule-checking.

    Returns:
        Either: The result of the rule-checking.

    """

    variable = state["variable"]
    period = state["period"]

    if (
        variable.definition_period in (periods.MONTH, periods.DAY)
        and period.unit == periods.WEEK
    ):
        return commons.either.fail(
            f"Unable to compute variable '{variable.name}' for period "
            f"{period}, as {period} and {variable.definition_period} are "
            "incompatible periods. You can, however, change the requested "
            "period to 'period.this_year'."
        )

    return commons.either.succeed(state)


def _check_periods_compatibility_2(state: _State) -> Either:
    """When definition period is week/weekday and period is month.

    Examples:
        >>> from openfisca_core import entities, periods, variables

        >>> entity = entities.SingleEntity("", "", "", "")

        >>> class Variable(variables.Variable):
        ...    definition_period = periods.YEAR
        ...    entity = entity
        ...    value_type = int

        >>> variable = Variable()
        >>> period = periods.period("2020-01")
        >>> state = {"variable": variable, "period": period}

        >>> _check_periods_compatibility_2(state)
        Success(_value={'variable': ..., 'period': ...})

        >>> variable.definition_period = periods.WEEKDAY
        >>> _check_periods_compatibility_2(state)
        Failure(_value="Unable to compute variable 'Variable' for period 2...")

    Args:
        state(_State): The state of the rule-checking.

    Returns:
        Either: The result of the rule-checking.

    """

    variable = state["variable"]
    period = state["period"]

    if (
        variable.definition_period in (periods.WEEK, periods.WEEKDAY)
        and period.unit == periods.MONTH
    ):
        return commons.either.fail(
            f"Unable to compute variable '{variable.name}' for period "
            f"{period}, as {period} and {variable.definition_period} are "
            "incompatible periods. You can, however, change the requested "
            "period to 'period.this_year' or 'period.first_week'."
        )

    return commons.either.succeed(state)
