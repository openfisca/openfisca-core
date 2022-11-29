"""Data types and protocols used by OpenFisca Core.

The type definitions included in this sub-package are intended for
contributors, to help them better understand and document contracts
and expected behaviours.

Official Public API:
    * :attr:`.Array`
    * ``ArrayLike``
    * :attr:`.Cache`
    * :attr:`.Entity`
    * :attr:`.Formula`
    * :attr:`.Holder`
    * :attr:`.Instant`
    * :attr:`.ParameterNodeAtInstant`
    * :attr:`.Params`
    * :attr:`.Period`
    * :attr:`.Population`
    * :attr:`.Role`,
    * :attr:`.Simulation`,
    * :attr:`.TaxBenefitSystem`
    * :attr:`.Variable`

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

from ._data import (  # noqa: F401
    Array,
    ArrayLike,
    )

from ._domain import (  # noqa: F401
    Entity,
    Formula,
    Holder,
    Instant,
    ParameterNodeAtInstant,
    Params,
    Period,
    Population,
    Role,
    Simulation,
    TaxBenefitSystem,
    Variable,
    )

__all__ = [
    "Array",
    "ArrayLike",
    "Entity",
    "Formula",
    "Holder",
    "Instant",
    "ParameterNodeAtInstant",
    "Params",
    "Period",
    "Population",
    "Role",
    "Simulation",
    "TaxBenefitSystem",
    "Variable",
    ]
