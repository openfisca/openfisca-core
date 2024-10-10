from . import types as t


class EnumMemberNotFoundError(IndexError):
    """Raised when a member is not found in an enum."""

    def __init__(self, enum_class: type[t.Enum], value: str) -> None:
        msg = (
            f"Member {value} not found in enum '{enum_class.__name__}'. "
            f"Possible values are: {', '.join(enum_class.names[:-1])}, and "
            f"{enum_class.names[-1]!s}; or their corresponding indices: "
            f"{', '.join(enum_class.indices[:-1].astype(t.StrDType))}, and "
            f"{enum_class.indices[-1]!s}."
        )
        super().__init__(msg)


__all__ = ["EnumMemberNotFoundError"]
