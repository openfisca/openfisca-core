from .projector import Projector


class UniqueRoleToEntityProjector(Projector):
    """For instance famille.declarant_principal."""

    def __init__(self, entity, role, parent=None) -> None:
        self.target_entity = entity
        self.reference_entity = entity.members
        self.parent = parent
        self.role = role

    def transform(self, result):
        return self.target_entity.value_from_person(result, self.role)
