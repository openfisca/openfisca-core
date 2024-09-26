from collections.abc import Sequence

from openfisca_core.types import DateUnit, Instant, InstantStr, Period, PeriodStr


class _SeqIntMeta(type):
    def __instancecheck__(self, arg: Sequence[object]) -> bool:
        try:
            return bool(arg) and all(isinstance(item, int) for item in arg)
        except TypeError:
            return False


class SeqInt(list[int], metaclass=_SeqIntMeta): ...


__all__ = [
    "DateUnit",
    "Instant",
    "InstantStr",
    "Period",
    "PeriodStr",
    "SeqInt",
]
