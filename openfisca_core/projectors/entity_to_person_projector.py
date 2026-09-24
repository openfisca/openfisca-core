from .projector import Projector


class EntityToPersonProjector(Projector):
    """For instance person.family."""

    def __init__(self, membership, parent=None) -> None:
        self.membership = membership
        self.reference_entity = membership.population
        self.parent = parent

    def transform(self, result):
        return self.membership.project(result)
