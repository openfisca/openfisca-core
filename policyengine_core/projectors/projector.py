from typing import TYPE_CHECKING

from policyengine_core.projectors import helpers

if TYPE_CHECKING:
    from policyengine_core.populations import Population

from numpy.typing import ArrayLike


class Projector:
    reference_entity: "Population" = None
    parent: "Projector" = None

    def __getattr__(self, attribute):
        projector = helpers.get_projector_from_shortcut(
            self.reference_entity, attribute, parent=self
        )
        if projector:
            return projector

        reference_attr = getattr(self.reference_entity, attribute)
        if not hasattr(reference_attr, "projectable"):
            return reference_attr

        def projector_function(*args, **kwargs):
            result = reference_attr(*args, **kwargs)
            return self.transform_and_bubble_up(result)

        return projector_function

    def __call__(self, *args, **kwargs):
        result = self.reference_entity(*args, **kwargs)
        return self.transform_and_bubble_up(result)

    def transform_and_bubble_up(self, result):
        transformed_result = self.transform(result)
        if self.parent is None:
            return transformed_result
        else:
            return self.parent.transform_and_bubble_up(transformed_result)

    def transform(self, result: ArrayLike):
        return NotImplementedError()
