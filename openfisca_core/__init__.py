"""The most widely adopted free and open-source engine to write rules as code."""

from openfisca_core.commons import (
    apply_thresholds,
    average_rate,
    concat,
    marginal_rate,
    switch,
)

from . import types
from .experimental import MemoryConfig
from .simulations import (
    Simulation,
    SimulationBuilder,
    calculate_output_add,
    calculate_output_divide,
    check_type,
    transform_to_strict_syntax,
)

__all__ = [
    "MemoryConfig",
    "Simulation",
    "SimulationBuilder",
    "apply_thresholds",
    "average_rate",
    "calculate_output_add",
    "calculate_output_divide",
    "check_type",
    "concat",
    "marginal_rate",
    "switch",
    "transform_to_strict_syntax",
    "types",
]
