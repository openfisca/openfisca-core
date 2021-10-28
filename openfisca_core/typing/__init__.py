"""Data types and protocols used by OpenFisca Core.

The type definitions included in this sub-package are intented for
contributors, to help them better understand and document contracts
and expected behaviours.

Official Public API:
    * :data:`.ArrayLike`
    * :attr:`.ArrayType`
    * :class:`.FormulaProtocol`
    * :class:`.HolderProtocol`
    * :class:`.PeriodProtocol`
    * :class:`.PopulationProtocol`
    * :class:`.TaxBenefitSystemProtocol`
    * :class:`.FrameSchema`
    * :class:`.OptionsSchema`
    * :class:`.TestSchema`


Note:
    How imports are being used today::

        from openfisca_core.typing import *  # Bad
        from openfisca_core.typing.data_types.arrays import ArrayLike  # Bad


    The previous examples provoke cyclic dependency problems, that prevents us
    from modularizing the different components of the library, so as to make
    them easier to test and to maintain.

    How could them be used after the next major release::

        from openfisca_core.typing import ArrayLike

        ArrayLike # Good: import types as publicly exposed

    .. seealso:: `PEP8#Imports`_ and `OpenFisca's Styleguide`_.

    .. _PEP8#Imports:
        https://www.python.org/dev/peps/pep-0008/#imports

    .. _OpenFisca's Styleguide:
        https://github.com/openfisca/openfisca-core/blob/master/STYLEGUIDE.md

"""

# Official Public API

from ._types import (  # noqa: F401
    ArrayLike,
    ArrayType,
    )

from ._protocols import (  # noqa: F401
    FormulaProtocol,
    HolderProtocol,
    PeriodProtocol,
    PopulationProtocol,
    TaxBenefitSystemProtocol,
    )

from ._schemas import (  # noqa: F401
    FrameSchema,
    OptionsSchema,
    TestSchema,
    )

__all__ = [
    "ArrayLike",
    "ArrayType",
    "FormulaProtocol",
    "HolderProtocol",
    "PeriodProtocol",
    "PopulationProtocol",
    "TaxBenefitSystemProtocol",
    "FrameSchema",
    "OptionsSchema",
    "TestSchema",
    ]
