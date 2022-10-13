from datetime import date

from numpy import (
    logical_not as not_,
    maximum as max_,
    minimum as min_,
    round as round_,
    select,
    where,
)

from policyengine_core.holders import (
    set_input_dispatch_by_period,
    set_input_divide_by_period,
)

from policyengine_core.enums import Enum

from policyengine_core.parameters import (
    load_parameter_file,
    ParameterNode,
    ParameterScale,
    ParameterScaleBracket,
    Parameter,
)

from policyengine_core.periods import (
    DAY,
    MONTH,
    YEAR,
    ETERNITY,
    period,
)
from policyengine_core.populations import ADD, DIVIDE
from policyengine_core.reforms import Reform

from policyengine_core.simulations import (
    calculate_output_add,
    calculate_output_divide,
)

from policyengine_core.variables import Variable, QuantityType

STOCK = QuantityType.STOCK
FLOW = QuantityType.FLOW

from policyengine_core.commons.formulas import *
