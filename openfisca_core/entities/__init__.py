"""Provides a way of representing the entities of a rule system.

Each rule system is comprised by legislation and regulations to be applied upon
"someone". In legal and economical terms, "someone" is referred to as people:
individuals, families, tax households, companies, and so on.

Official Public API:
    * :class:`.Entity`
    * :class:`.GroupEntity`
    * :class:`.Role`
    * :func:`.build_entity`
    * :func:`.check_role_validity`

Deprecated:
    * :meth:`.Entity.set_tax_benefit_system`
    * :meth:`.Entity.get_variable`
    * :meth:`.Entity.check_variable_defined_for_entity`
    * :meth:`.Entity.check_role_validity`

Note:
    The ``deprecated`` features are kept so as to give time to users to
    migrate, and could be definitely removed from the codebase in a future
    major release.

Note:
    How imports are being used today::

        from openfisca_core.entities import *  # Bad
        from openfisca_core.entities.helpers import build_entity  # Bad
        from openfisca_core.entities.role import Role  # Bad

    The previous examples provoke cyclic dependency problems, that prevents us
    from modularizing the different components of the library, so as to make
    them easier to test and to maintain.

    How could them be used after the next major release::

        from openfisca_core import entities
        from openfisca_core.entities import Role

        Role()  # Good: import classes as publicly exposed
        entities.build_entity()  # Good: use functions as publicly exposed

    .. seealso:: `PEP8#Imports`_ and `OpenFisca's Styleguide`_.

    .. _PEP8#Imports:
        https://www.python.org/dev/peps/pep-0008/#imports

    .. _OpenFisca's Styleguide:
        https://github.com/openfisca/openfisca-core/blob/master/STYLEGUIDE.md

"""

# Official Public API

from .entity import Entity  # noqa: F401
from .group_entity import GroupEntity  # noqa: F401
from .role import Role  # noqa: F401
from .helpers import build_entity, check_role_validity  # noqa: F401

__all__ = ["Entity", "GroupEntity", "Role"]
__all__ = ["build_entity", "check_role_validity", *__all__]
