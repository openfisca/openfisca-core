"""Common tools for contributors and users.

The tools included in this sub-package are intented, at the same time, to help
contributors who maintain OpenFisca Core, and to help users building their own
systems.

Official Public API:
    * :class:`.deprecated`
    * :func:`.apply_thresholds`
    * :func:`.average_rate`
    * :func:`.concat`
    * :func:`.empty_clone`
    * :func:`.marginal_rate`
    * :func:`.stringify_array`
    * :func:`.switch`

Deprecated:
    * :class:`.Dummy`

Note:
    The ``deprecated`` imports are transitional, as so to ensure non-breaking
    changes, and could be definitely removed from the codebase in the next
    major release.

Note:
    How imports are being used today::

        from openfisca_core.commons import *  # Bad
        from openfisca_core.commons.formulas import switch  # Bad
        from openfisca_core.commons.decorators import deprecated  # Bad

    The previous examples provoke cyclic dependency problems, that prevents us
    from modularizing the different components of the library, so as to make
    them easier to test and to maintain.

    How could them be used after the next major release::

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

# Official Public API

from .decorators import deprecated  # noqa: F401
from .formulas import apply_thresholds, concat, switch  # noqa: F401
from .misc import empty_clone, stringify_array  # noqa: F401
from .rates import average_rate, marginal_rate  # noqa: F401

__all__ = ["deprecated"]
__all__ = ["apply_thresholds", "concat", "switch", *__all__]
__all__ = ["empty_clone", "stringify_array", *__all__]
__all__ = ["average_rate", "marginal_rate", *__all__]

# Deprecated

from .dummy import Dummy  # noqa: F401

__all__ = ["Dummy", *__all__]
