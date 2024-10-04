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

from . import typing
from .entity_to_person_projector import EntityToPersonProjector
from .first_person_to_entity_projector import FirstPersonToEntityProjector
from .helpers import get_projector_from_shortcut, projectable
from .projector import Projector
from .unique_role_to_entity_projector import UniqueRoleToEntityProjector

__all__ = [
    "EntityToPersonProjector",
    "FirstPersonToEntityProjector",
    "get_projector_from_shortcut",
    "projectable",
    "Projector",
    "UniqueRoleToEntityProjector",
    "typing",
]
