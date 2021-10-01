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

from openfisca_core.errors import ParameterNotFound, ParameterParsingError  # noqa: F401


from .config import (  # noqa: F401
    ALLOWED_PARAM_TYPES,
    COMMON_KEYS,
    FILE_EXTENSIONS,
    date_constructor,
    dict_no_duplicate_constructor,
    )

from .at_instant_like import AtInstantLike  # noqa: F401
from .helpers import contains_nan, load_parameter_file  # noqa: F401
from .parameter_at_instant import ParameterAtInstant  # noqa: F401
from .parameter_node_at_instant import ParameterNodeAtInstant  # noqa: F401
from .vectorial_parameter_node_at_instant import VectorialParameterNodeAtInstant  # noqa: F401
from .parameter import Parameter  # noqa: F401
from .parameter_node import ParameterNode  # noqa: F401
from .parameter_scale import ParameterScale, ParameterScale as Scale  # noqa: F401
from .parameter_scale_bracket import ParameterScaleBracket, ParameterScaleBracket as Bracket  # noqa: F401
from .values_history import ValuesHistory  # noqa: F401
