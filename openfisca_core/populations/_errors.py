from . import types as t


class InvalidArraySizeError(ValueError):
    """Raised when an array has an invalid size."""

    def __init__(self, array: t.VarArray, entity: t.EntityKey, count: int) -> None:
        msg = (
            f"Input {array} is not a valid value for the entity {entity} "
            f"(size = {array.size} != {count} = count)."
        )
        super().__init__(msg)


class PeriodValidityError(ValueError):
    """Raised when a period is not valid."""

    def __init__(
        self,
        variable_name: t.VariableName,
        filename: str,
        line_number: int,
        line_of_code: int,
    ) -> None:
        msg = (
            f'You requested computation of variable "{variable_name}", but '
            f'you did not specify on which period in "{filename}:{line_number}": '
            f"{line_of_code}. When you request the computation of a variable "
            "within a formula, you must always specify the period as the second "
            'parameter. The convention is to call this parameter "period". For '
            'example: computed_salary = person("salary", period). More information at '
            "<https://openfisca.org/doc/coding-the-legislation/35_periods.html#periods-in-variable-definition>."
        )
        super().__init__(msg)


__all__ = ["InvalidArraySizeError", "PeriodValidityError"]
