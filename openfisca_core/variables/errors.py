import os


class FormulaNameError(ValueError):
    """Raised when a formula name is invalid."""

    def __init__(self, name: str):
        message = (
            "Unrecognized formula name. Expecting 'formula_YYYY'",
            "'formula_YYYY_MM', or 'formula_YYYY_MM_DD', where YYYY, MM and",
            f"DD are year, month and day. Found: '{name}'.",
        )

        super().__init__(os.linesep.join(message))
