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

from .callables import (  # noqa: F401
    FormulaType,
    ParamsType,
    )

from .data_types import (  # noqa: F401
    ArrayType,
    ArrayLike,
    RoleLike,
    )

from .protocols import (  # noqa: F401
    Aggregatable,
    Buildable,
    Descriptable,
    Personifiable,
    Representable,
    Rolifiable,
    )
