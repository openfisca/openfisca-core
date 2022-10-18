from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from policyengine_core.populations import Population

from numpy.typing import ArrayLike

from policyengine_core.projectors.projector import Projector


class EntityToPersonProjector(Projector):
    """For instance person.family."""

    def __init__(self, entity: "Population", parent: Projector = None):
        self.reference_entity = entity
        self.parent = parent

    def transform(self, result: ArrayLike) -> ArrayLike:
        return self.reference_entity.project(result)
