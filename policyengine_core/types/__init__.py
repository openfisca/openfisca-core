"""Data types and protocols used by OpenFisca Core.

The type definitions included in this sub-package are intented for
contributors, to help them better understand and document contracts
and expected behaviours.

Official Public API:
    * ``ArrayLike``
    * :attr:`.ArrayType`

Note:
    How imports are being used today::

        from policyengine_core.types import *  # Bad
        from policyengine_core.types.data_types.arrays import ArrayLike  # Bad


    The previous examples provoke cyclic dependency problems, that prevents us
    from modularizing the different components of the library, so as to make
    them easier to test and to maintain.

    How could them be used after the next major release::

        from policyengine_core.types import ArrayLike

        ArrayLike # Good: import types as publicly exposed

    .. seealso:: `PEP8#Imports`_ and `OpenFisca's Styleguide`_.

    .. _PEP8#Imports:
        https://www.python.org/dev/peps/pep-0008/#imports

    .. _OpenFisca's Styleguide:
        https://github.com/openfisca/openfisca-core/blob/master/STYLEGUIDE.md

"""

# Official Public API

from .data_types import ArrayLike, ArrayType

__all__ = ["ArrayLike", "ArrayType"]
