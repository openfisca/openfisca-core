# Transitional imports to ensure non-breaking changes.
# Could be deprecated in the next major release.
#
# How imports are being used today:
#
#   >>> from openfisca_core.module import symbol
#
# The previous example provokes cyclic dependency problems
# that prevent us from modularizing the different components
# of the library so to make them easier to test and to maintain.
#
# How could them be used after the next major release:
#
#   >>> from openfisca_core import module
#   >>> module.symbol()
#
# And for classes:
#
#   >>> from openfisca_core.module import Symbol
#   >>> Symbol()
#
# See: https://www.python.org/dev/peps/pep-0008/#imports

from openfisca_core.errors import CycleError, NaNCreationError, SpiralError

from .helpers import (
    calculate_output_add,
    calculate_output_divide,
    check_type,
    transform_to_strict_syntax,
)
from .simulation import Simulation
from .simulation_builder import SimulationBuilder

__all__ = [
    "CycleError",
    "NaNCreationError",
    "Simulation",
    "SimulationBuilder",
    "SpiralError",
    "calculate_output_add",
    "calculate_output_divide",
    "check_type",
    "transform_to_strict_syntax",
]
