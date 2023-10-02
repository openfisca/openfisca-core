from __future__ import annotations

from numpy.typing import NDArray
from typing import Any, cast

import dataclasses
import inspect

from ..typing import Formula2, Formula3, Instant, Params, Population


@dataclasses.dataclass(frozen=True)
class RunFormula:
    """Run a Variable's given Formula."""

    #: The formula we want to run.
    formula: Formula3 | Formula2 | None = None

    def __call__(
        self, population: Population, instant: Instant, params: Params
    ) -> NDArray[Any] | None:
        if self.formula is None:
            return None

        if self.__arity() == 3:
            return cast(Formula3, self.formula)(population, instant, params)

        else:
            return cast(Formula2, self.formula)(population, instant)

    def __arity(self) -> int:
        return len(inspect.getfullargspec(self.formula).args)
