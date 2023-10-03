from .entity import Entity
from .group_entity import GroupEntity


def build_entity(
    key,
    plural,
    label,
    doc="",
    roles=None,
    is_person=False,
    class_override=None,
    containing_entities=(),
):
    if is_person:
        return Entity(key, plural, label, doc)
    else:
        return GroupEntity(
            key, plural, label, doc, roles, containing_entities=containing_entities
        )
