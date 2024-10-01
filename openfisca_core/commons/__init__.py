"""Common tools for contributors and users.

The tools in this sub-package are intended, to help both contributors
to OpenFisca Core and to country packages.

Official Public API:
    * :func:`.apply_thresholds`
    * :func:`.average_rate`
    * :func:`.concat`
    * :func:`.empty_clone`
    * :func:`.eval_expression`
    * :func:`.marginal_rate`
    * :func:`.stringify_array`
    * :func:`.switch`

Deprecated:
    * :class:`.Dummy`

Note:
    The ``deprecated`` imports are transitional, in order to ensure non-breaking
    changes, and could be removed from the codebase in the next
    major release.

Note:
    How imports are being used today::

        from openfisca_core.commons import *  # Bad
        from openfisca_core.commons.formulas import switch  # Bad
        from openfisca_core.commons.decorators import deprecated  # Bad


    The previous examples provoke cyclic dependency problems, that prevent us
    from modularizing the different components of the library, which would make
    them easier to test and to maintain.

    How they could be used in a future release::

        from openfisca_core import commons
        from openfisca_core.commons import deprecated

        deprecated()  # Good: import classes as publicly exposed
        commons.switch()  # Good: use functions as publicly exposed

    .. seealso:: `PEP8#Imports`_ and `OpenFisca's Styleguide`_.

    .. _PEP8#Imports:
        https://www.python.org/dev/peps/pep-0008/#imports

    .. _OpenFisca's Styleguide:
        https://github.com/openfisca/openfisca-core/blob/master/STYLEGUIDE.md

"""

from . import types
from .dummy import Dummy
from .formulas import apply_thresholds, concat, switch
from .misc import empty_clone, eval_expression, stringify_array
from .rates import average_rate, marginal_rate

__all__ = [
    "Dummy",
    "apply_thresholds",
    "average_rate",
    "concat",
    "empty_clone",
    "eval_expression",
    "marginal_rate",
    "stringify_array",
    "switch",
    "types",
]
