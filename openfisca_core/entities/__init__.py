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
#   >>> from openfisca_core import module
#   >>> module.Symbol()
#
# See: https://www.python.org/dev/peps/pep-0008/#imports

from . import types
from .entity import Entity
from .group_entity import GroupEntity
from .helpers import build_entity, find_role
from .role import Role

SingleEntity = Entity

__all__ = [
    "Entity",
    "SingleEntity",
    "GroupEntity",
    "Role",
    "build_entity",
    "find_role",
    "types",
]
