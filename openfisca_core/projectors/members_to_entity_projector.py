from .projector import Projector


class MembersToEntityProjector(Projector):
    """For instance family.people."""

    def __init__(self, membership, parent=None) -> None:
        self.membership = membership
        self.reference_entity = membership.members
        self.parent = parent

    def transform(self, result):
        return result
