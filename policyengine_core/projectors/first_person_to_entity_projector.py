from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from policyengine_core.populations import GroupPopulation
from policyengine_core.projectors.projector import Projector


class FirstPersonToEntityProjector(Projector):
    """For instance famille.first_person."""

    def __init__(self, entity: "GroupPopulation", parent: Projector = None):
        self.target_entity = entity
        self.reference_entity = entity.members
        self.parent = parent

    def transform(self, result):
        return self.target_entity.value_from_first_person(result)
