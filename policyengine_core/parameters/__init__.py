# Transitional imports to ensure non-breaking changes.
# Could be deprecated in the next major release.
#
# How imports are being used today:
#
#   >>> from policyengine_core.module import symbol
#
# The previous example provokes cyclic dependency problems
# that prevent us from modularizing the different components
# of the library so to make them easier to test and to maintain.
#
# How could them be used after the next major release:
#
#   >>> from policyengine_core import module
#   >>> module.symbol()
#
# And for classes:
#
#   >>> from policyengine_core.module import Symbol
#   >>> Symbol()
#
# See: https://www.python.org/dev/peps/pep-0008/#imports

from policyengine_core.errors import (
    ParameterNotFound,
    ParameterParsingError,
)


from .config import (
    ALLOWED_PARAM_TYPES,
    COMMON_KEYS,
    FILE_EXTENSIONS,
    date_constructor,
    dict_no_duplicate_constructor,
)

from .at_instant_like import AtInstantLike
from .helpers import contains_nan, load_parameter_file
from .parameter_at_instant import ParameterAtInstant
from .parameter_node_at_instant import ParameterNodeAtInstant
from .vectorial_parameter_node_at_instant import (
    VectorialParameterNodeAtInstant,
)
from .parameter import Parameter
from .parameter_node import ParameterNode
from .parameter_scale import (
    ParameterScale,
    ParameterScale as Scale,
)
from .parameter_scale_bracket import (
    ParameterScaleBracket,
    ParameterScaleBracket as Bracket,
)
from .values_history import ValuesHistory
