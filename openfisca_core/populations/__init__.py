"""Transitional imports to ensure non-breaking changes.

These imports could be deprecated in the next major release.

Currently, imports are used in the following way::

    from openfisca_core.module import symbol

This example causes cyclic dependency problems, which prevent us from
modularising the different components of the library and make them easier to
test and maintain.

After the next major release, imports could be used in the following way::

    from openfisca_core import module
    module.symbol()

And for classes::

    from openfisca_core.module import Symbol
    Symbol()

.. seealso:: `PEP8#Imports`_ and `OpenFisca's Styleguide`_.

.. _PEP8#Imports:
    https://www.python.org/dev/peps/pep-0008/#imports

.. _OpenFisca's Styleguide:
    https://github.com/openfisca/openfisca-core/blob/master/STYLEGUIDE.md

"""

from openfisca_core.projectors import (
    Projector,
    EntityToPersonProjector,
    FirstPersonToEntityProjector,
    UniqueRoleToEntityProjector,
)

from openfisca_core.projectors.helpers import (
    projectable,
    get_projector_from_shortcut,
)

from .config import ADD, DIVIDE
from .population import Population
from .group_population import GroupPopulation
