# The simulation builder module has been deprecated since X.X.X,
# and will be removed in the future.
#
# Module's contents have been moved to the simulation module.
#
# The following are transitional imports to ensure non-breaking changes.
# Could be deprecated in the next major release.

from openfisca_core.simulations import (    # noqa: F401
    Simulation,
    SimulationBuilder,
    calculate_output_add,
    calculate_output_divide,
    check_type,
    transform_to_strict_syntax,
    )
