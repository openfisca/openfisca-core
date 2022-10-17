from datetime import date

from numpy import logical_not as not_
from numpy import maximum as max_
from numpy import minimum as min_
from numpy import round as round_
from numpy import select, where

from policyengine_core.enums import Enum
from policyengine_core.holders import (
    set_input_dispatch_by_period,
    set_input_divide_by_period,
)
from policyengine_core.parameters import (
    Parameter,
    ParameterNode,
    ParameterScale,
    ParameterScaleBracket,
    load_parameter_file,
)
from policyengine_core.periods import DAY, ETERNITY, MONTH, YEAR, period
from policyengine_core.populations import ADD, DIVIDE
from policyengine_core.reforms import Reform
from policyengine_core.simulations import (
    calculate_output_add,
    calculate_output_divide,
)
from policyengine_core.variables import QuantityType, Variable

STOCK = QuantityType.STOCK
FLOW = QuantityType.FLOW

from policyengine_core.commons.formulas import *
