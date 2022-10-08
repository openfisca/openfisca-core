# Transitional imports to ensure non-breaking changes.
# Could be deprecated in the next major release.
#
# How imports are being used today:
#
#   >>> from policyengine_core.module import symbol
#
# The previous example provokes cyclic dependency problems
# that prevent us from modularizing the different components
# of the library so to make them easier to test and to maintain.
#
# How could them be used after the next major release:
#
#   >>> from policyengine_core import module
#   >>> module.symbol()
#
# And for classes:
#
#   >>> from policyengine_core.module import Symbol
#   >>> Symbol()
#
# See: https://www.python.org/dev/peps/pep-0008/#imports

from .helpers import projectable, get_projector_from_shortcut
from .projector import Projector
from .entity_to_person_projector import EntityToPersonProjector
from .first_person_to_entity_projector import (
    FirstPersonToEntityProjector,
)
from .unique_role_to_entity_projector import (
    UniqueRoleToEntityProjector,
)
