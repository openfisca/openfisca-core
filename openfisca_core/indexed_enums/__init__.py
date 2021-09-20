"""Enumerations for variables with a limited set of possible values.

These include:
    * Highest academic level: high school, associate degree, bachelor’s
      degree, master’s degree, doctorate…
    * A household housing occupancy status: owner, tenant, free-lodger,
      homeless…
    * The main occupation of a person: employee, freelancer, retired, student,
      unemployed…

Official Public API:
    * :attr:`.ENUM_ARRAY_DTYPE`
    * :class:`.EnumArray`
    * :class:`.Enum`

Note:
    How imports are being used today::

        from openfisca_core.indexed_enums import *  # Bad
        from openfisca_core.indexed_enums.config import ENUM_ARRAY_DTYPE  # Bad
        from openfisca_core.ndexed_enums.Enum import Enum  # Bad

    The previous examples provoke cyclic dependency problems, that prevents us
    from modularizing the different components of the library, so as to make
    them easier to test and to maintain.

    How could them be used after the next major release::

        from openfisca_core import indexed_enums
        from openfisca_core.indexed_enums import Enum

        Enum()  # Good: import classes as publicly exposed
        indexed_enums.ENUM_ARRAY_DTYPE  # Good: use attrs as publicly exposed

    .. seealso:: `PEP8#Imports`_ and `OpenFisca's Styleguide`_.

    .. _PEP8#Imports:
        https://www.python.org/dev/peps/pep-0008/#imports

    .. _OpenFisca's Styleguide:
        https://github.com/openfisca/openfisca-core/blob/master/STYLEGUIDE.md

"""

# Official Public API

from .config import ENUM_ARRAY_DTYPE  # noqa: F401
from .enum_array import EnumArray  # noqa: F401
from .enum import Enum  # noqa: F401

__all__ = ["ENUM_ARRAY_DTYPE", "EnumArray", "Enum"]
