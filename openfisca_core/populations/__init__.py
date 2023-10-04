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

from openfisca_core.projectors import (
    EntityToPersonProjector,
    FirstPersonToEntityProjector,
    Projector,
    UniqueRoleToEntityProjector,
)
from openfisca_core.projectors.helpers import get_projector_from_shortcut, projectable

from .config import ADD, DIVIDE
from .group_population import GroupPopulation
from .population import Population

__all__ = [
    "ADD",
    "DIVIDE",
    "EntityToPersonProjector",
    "FirstPersonToEntityProjector",
    "GroupPopulation",
    "Population",
    "Projector",
    "UniqueRoleToEntityProjector",
    "get_projector_from_shortcut",
    "projectable",
]
