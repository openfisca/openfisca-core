"""Provides a way of representing the entities of a rule system.

Each rule system is comprised by legislation and regulations to be applied upon
"someone". In legal and economical terms, "someone" is referred to as people:
individuals, families, tax households, companies, and so on.

People can be either human or non-human, that is a legal entity, also referred
to as a legal person. Human or non-human, a person is an atomic element of a
rule system: for example, in most legislations, a salary is invariably owed
to an indivual, and payroll taxes by a company, as a juridical person. In
OpenFisca, that atomic element is represented as an :class:`.Entity`.

In other cases, legal and regulatory rules are defined for groups or clusters
of people: for example, income tax is usually due by a tax household, that is
a group of individuals. There may also be fiduciary entities where the members,
legal entities, are collectively liable for a property tax. In OpenFisca, those
cluster elements are represented as a :class:`.GroupEntity`.

In the latter case, the atomic members of a given group may have a different
:class:`Role` in the context of a specific rule: for example, income tax
is due, in some legislations, by a tax household, where we find different
roles as the declarant, the spouse, the children, and so on…

What's important is that each rule, or in OpenFisca, a :class:`.Variable`,
is defined either for an :class:`.Entity` or for a :class:`.GroupEntity`,
and in the latter case, the way the rule is going to be applied depends
on the attributes and roles of the members of the group.

Finally, there is a distinction to be made between the "abstract" entities
described in a rule system, for example an individual, as in "any"
individual, and an actual individual, like Mauko, Andrea, Mehdi, Seiko,
or José.

This module provides tools for modelling the former. For the actual
"simulation" or "application" of any given :class:`.Variable` to a
concrete individual or group of individuals, see :class:`.Population`
and :class:`.GroupPopulation`.

Official Public API:
    * :class:`.Entity`
    * :class:`.GroupEntity`
    * :class:`.Role`
    * :func:`.build_entity`
    * :func:`.check_role_validity`

Deprecated:
    * :meth:`.Entity.set_tax_benefit_system`
    * :meth:`.Entity.check_role_validity`

Note:
    The ``deprecated`` imports are transitional, in order to ensure
    non-breaking changes, and could be removed from the codebase in the next
    major release.

Note:
    How imports are being used today::

        from openfisca_core.entities import *  # Bad
        from openfisca_core.entities.helpers import build_entity  # Bad
        from openfisca_core.entities.role import Role  # Bad

    The previous examples provoke cyclic dependency problems, that prevent us
    from modularizing the different components of the library, which would make
    them easier to test and to maintain.

    How they could be used in a future release::

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

from .helpers import (  # noqa: F401
    Entity,
    GroupEntity,
    Role,
    build_entity,
    check_role_validity,
    )

__all__ = ["Entity", "GroupEntity", "Role"]
__all__ = ["build_entity", "check_role_validity", *__all__]
