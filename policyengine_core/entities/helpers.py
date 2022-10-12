from openfisca_core import entities


def build_entity(key, plural, label, doc = "", roles = None, is_person = False, class_override = None, containing_entities = ()):
    if is_person:
        return entities.Entity(key, plural, label, doc)
    else:
        return entities.GroupEntity(key, plural, label, doc, roles, containing_entities = containing_entities)
