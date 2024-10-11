from . import types as t


class InvalidArraySizeError(ValueError):
    """Raised when an array has an invalid size."""

    def __init__(self, array: t.FloatArray, entity: t.EntityKey, count: int) -> None:
        msg = (
            f"Input {array} is not a valid value for the entity {entity} "
            f"(size = {array.size} != {count} = count)."
        )
        super().__init__(msg)


__all__ = ["InvalidArraySizeError"]
