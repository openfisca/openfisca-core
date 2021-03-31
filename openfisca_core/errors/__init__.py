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
#   >>> from openfisca_core import module
#   >>> module.Symbol()
#
# See: https://www.python.org/dev/peps/pep-0008/#imports

from .parameter_not_found_error import ParameterNotFoundError, ParameterNotFoundError as ParameterNotFound  # noqa: F401
from .parameter_parsing_error import ParameterParsingError  # noqa: F401
from .period_mismatch_error import PeriodMismatchError  # noqa: F401
from .situation_parsing_error import SituationParsingError  # noqa: F401
from .variable_not_found_error import VariableNotFoundError, VariableNotFoundError as VariableNotFound  # noqa: F401
