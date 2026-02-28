from __future__ import annotations

from collections.abc import Iterable

import warnings

from ._errors import MemoryConfigWarning


class MemoryConfig:
    """Experimental memory configuration."""

    #: Maximum memory occupation allowed.
    max_memory_occupation: float

    #: Priority variables.
    priority_variables: frozenset[str]

    #: Variables to drop.
    variables_to_drop: frozenset[str]

    #: Default number of LRU snapshots for as_of variables (None = use holder default).
    asof_max_snapshots: int | None

    def __init__(
        self,
        max_memory_occupation: str | float,
        priority_variables: Iterable[str] = frozenset(),
        variables_to_drop: Iterable[str] = frozenset(),
        asof_max_snapshots: int | None = None,
    ) -> None:
        message = [
            "Memory configuration is a feature that is still currently under "
            "experimentation. You are very welcome to use it and send us "
            "precious feedback, but keep in mind that the way it is used might "
            "change without any major version bump.",
        ]
        warnings.warn(" ".join(message), MemoryConfigWarning, stacklevel=2)

        self.max_memory_occupation = float(max_memory_occupation)
        if self.max_memory_occupation > 1:
            msg = "max_memory_occupation must be <= 1"
            raise ValueError(msg)
        self.max_memory_occupation_pc = self.max_memory_occupation * 100
        self.priority_variables = frozenset(priority_variables)
        self.variables_to_drop = frozenset(variables_to_drop)
        self.asof_max_snapshots = asof_max_snapshots
