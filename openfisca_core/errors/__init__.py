# Transitional imports to ensure non-breaking changes.
# Could be deprecated in the next major release.
#
# How imports are being used today:
#
#   >>> from openfisca_core.module import symbol
#
# The previous example provokes cyclic dependency problems
# that prevent us from modularizing the different components
# of the library so to make them easier to test and to maintain.
#
# How could them be used after the next major release:
#
#   >>> from openfisca_core import module
#   >>> module.symbol()
#
# And for classes:
#
#   >>> from openfisca_core.module import Symbol
#   >>> Symbol()
#
# See: https://www.python.org/dev/peps/pep-0008/#imports

from .cycle_error import CycleError
from .empty_argument_error import EmptyArgumentError
from .nan_creation_error import NaNCreationError
from .parameter_not_found_error import (
    ParameterNotFoundError,
    ParameterNotFoundError as ParameterNotFound,
)
from .parameter_parsing_error import ParameterParsingError
from .period_mismatch_error import PeriodMismatchError
from .situation_parsing_error import SituationParsingError
from .spiral_error import SpiralError
from .variable_name_config_error import (
    VariableNameConflictError,
    VariableNameConflictError as VariableNameConflict,
)
from .variable_not_found_error import (
    VariableNotFoundError,
    VariableNotFoundError as VariableNotFound,
)

__all__ = [
    "CycleError",
    "EmptyArgumentError",
    "NaNCreationError",
    "ParameterNotFound",  # Deprecated alias for "ParameterNotFoundError
    "ParameterNotFoundError",
    "ParameterParsingError",
    "PeriodMismatchError",
    "SituationParsingError",
    "SpiralError",
    "VariableNameConflict",  # Deprecated alias for "VariableNameConflictError"
    "VariableNameConflictError",
    "VariableNotFound",  # Deprecated alias for "VariableNotFoundError"
    "VariableNotFoundError",
]
