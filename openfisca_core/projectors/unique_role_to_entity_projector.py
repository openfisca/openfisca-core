from .projector import Projector


class UniqueRoleToEntityProjector(Projector):
    """For instance famille.declarant_principal."""

    def __init__(self, entity, role, parent=None, reference_entity=None) -> None:
        self.target_entity = entity
        self.reference_entity = reference_entity or entity.members
        self.parent = parent
        self.role = role

    def transform(self, result):
        return self.target_entity.value_from_person(result, self.role)
