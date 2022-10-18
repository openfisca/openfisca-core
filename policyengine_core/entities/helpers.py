from typing import List

from policyengine_core import entities
from policyengine_core.entities.entity import Entity


def build_entity(
    key: str,
    plural: str,
    label: str,
    doc: str = "",
    roles: List[str] = None,
    is_person: bool = False,
    containing_entities: List[str] = (),
) -> Entity:
    if is_person:
        return entities.Entity(key, plural, label, doc)
    else:
        return entities.GroupEntity(
            key,
            plural,
            label,
            doc,
            roles,
            containing_entities=containing_entities,
        )
