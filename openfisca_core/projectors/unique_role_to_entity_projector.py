from .projector import Projector


class UniqueRoleToEntityProjector(Projector):
    """For instance famille.declarant_principal."""

    def __init__(self, membership, role, parent=None) -> None:
        self.membership = membership
        self.reference_entity = membership.members
        self.parent = parent
        self.role = role

    def transform(self, result):
        return self.membership.value_from_person(result, self.role)
