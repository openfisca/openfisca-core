"""Provides a way of representing the entities of a rule system.

Each rule system is comprised by legislation and regulations to be applied upon
"someone". In legal and economical terms, "someone" is referred to as people:
individuals, families, tax households, companies, and so on.

"""

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

from .entity import Entity  # noqa: F401
from .group_entity import GroupEntity  # noqa: F401
from .role import Role  # noqa: F401
from .role_builder import RoleBuilder  # noqa: F401
from .helpers import build_entity, check_role_validity  # noqa: F401
