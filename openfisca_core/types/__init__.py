"""Data types and protocols used by OpenFisca Core.

The type definitions included in this sub-package are intented mostly for
contributors, to help them better document contracts and behaviours.

Official Public API:
    * :data:`.ArrayLike`
    * :attr:`.ArrayType`
    * :class:`.RoleLike`
    * :class:`.Builder`
    * :class:`.Descriptor`
    * :class:`.HasHolders`
    * :class:`.HasPlural`
    * :class:`.HasVariables`
    * :class:`.SupportsEncode`
    * :class:`.SupportsFormula`
    * :class:`.SupportsRole`

Note:
    How imports are being used today::

        from openfisca_core.types import *  # Bad
        from openfisca_core.types.data_types.arrays import ArrayLike  # Bad

    The previous examples provoke cyclic dependency problems, that prevents us
    from modularizing the different components of the library, so as to make
    them easier to test and to maintain.

    How could them be used after the next major release::

        from openfisca_core.types import ArrayLike

        ArrayLike # Good: import types as publicly exposed

    .. seealso:: `PEP8#Imports`_ and `OpenFisca's Styleguide`_.

    .. _PEP8#Imports:
        https://www.python.org/dev/peps/pep-0008/#imports

    .. _OpenFisca's Styleguide:
        https://github.com/openfisca/openfisca-core/blob/master/STYLEGUIDE.md

"""

# Official Public API

from .data_types import (  # noqa: F401
    ArrayLike,
    ArrayType,
    RoleLike,
    )

__all__ = ["ArrayLike", "ArrayType", "RoleLike"]

from .protocols import (  # noqa: F401
    Builder,
    Descriptor,
    HasHolders,
    HasPlural,
    HasVariables,
    SupportsEncode,
    SupportsFormula,
    SupportsRole,
    )

__all__ = ["Builder", "Descriptor", "HasHolders", "HasPlural", *__all__]
__all__ = ["HasVariables", "SupportsEncode", "SupportsFormula", *__all__]
__all__ = ["SupportsRole", *__all__]
