"""Links between entities (Many2One, One2Many, chaining).

This module implements a generic link system inspired by LIAM2, enriched
with OpenFisca's role semantics.  Links are orthogonal to the existing
GroupEntity/Projector machinery: current code keeps working unchanged,
and links provide additional capabilities (intra-entity links, chaining,
arbitrary named links).

Usage in a country package::

    from openfisca_core.links import Many2OneLink, One2ManyLink

    # Declare a person→person link (intra-entity)
    mother = Many2OneLink(
        name="mother",
        link_field="mother_id",
        target_entity_key="person",
    )

    # Declare a person→employer link (inter-entity)
    employer = Many2OneLink(
        name="employer",
        link_field="employer_id",
        target_entity_key="employer",
    )
"""

from .link import Link
from .many2one import Many2OneLink
from .one2many import One2ManyLink

__all__ = [
    "Link",
    "Many2OneLink",
    "One2ManyLink",
]
