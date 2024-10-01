"""Provide a way of representing the entities of a rule system.

Each rule system is comprised by legislation and regulations to be applied upon
"someone". In legal and economical terms, "someone" is referred to as people:
individuals, families, tax households, companies, and so on.

People can be either human or non-human, that is a legal entity, also referred
to as a legal person. Human or non-human, a person is an atomic element of a
rule system: for example, in most legislations, a salary is invariably owed
to an individual, and payroll taxes by a company, as a juridical person. In
OpenFisca, that atomic element is represented as an ``Entity``.

In other cases, legal and regulatory rules are defined for groups or clusters
of people: for example, income tax is usually due by a tax household, that is
a group of individuals. There may also be fiduciary entities where the members,
legal entities, are collectively liable for a property tax. In OpenFisca, those
cluster elements are represented as a ``GroupEntity``.

In the latter case, the atomic members of a given group may have a different
``Role`` in the context of a specific rule: for example, income tax
is due, in some legislations, by a tax household, where we find different
roles as the declarant, the spouse, the children, and so on…

What's important is that each rule, or in OpenFisca, a ``Variable``
is defined either for an ``.Entity`` or for a ``GroupEntity``,
and in the latter case, the way the rule is going to be applied depends
on the attributes and roles of the members of the group.

Finally, there is a distinction to be made between the "abstract" entities
described in a rule system, for example an individual, as in "any"
individual, and an actual individual, like Mauko, Andrea, Mehdi, Seiko,
or José.

This module provides tools for modelling the former. For the actual
"simulation" or "application" of any given ``Variable`` to a
concrete individual or group of individuals, see ``Population``
and ``GroupPopulation``.

"""

from . import types
from ._core_entity import CoreEntity
from .entity import Entity
from .group_entity import GroupEntity
from .helpers import build_entity, find_role
from .role import Role

SingleEntity = Entity
check_role_validity = CoreEntity.check_role_validity

__all__ = [
    "CoreEntity",
    "Entity",
    "GroupEntity",
    "Role",
    "SingleEntity",
    "build_entity",
    "check_role_validity",
    "find_role",
    "types",
]
