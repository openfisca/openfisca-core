from . import types as t


class EnumEncodingError(TypeError):
    """Raised when an enum is encoded with an unsupported type."""

    def __init__(self, enum_class: type[t.Enum], value: t.VarArray) -> None:
        msg = (
            f"Failed to encode \"{value}\" of type '{value[0].__class__.__name__}', "
            "as it is not supported. Please, try again with an array of "
            f"'{int.__name__}', '{str.__name__}', or '{enum_class.__name__}'."
        )
        super().__init__(msg)


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


__all__ = ["EnumEncodingError", "EnumMemberNotFoundError"]
