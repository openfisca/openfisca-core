from openfisca_core.projectors import Projector


class FirstPersonToEntityProjector(Projector):
    """For instance famille.first_person."""

    def __init__(self, entity, parent = None):
        self.target_entity = entity
        self.reference_entity = entity.members
        self.parent = parent

    def transform(self, result):
        return self.target_entity.value_from_first_person(result)
