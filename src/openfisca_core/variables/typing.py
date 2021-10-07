from typing import Callable, Union

import numpy

from openfisca_core.parameters import ParameterNodeAtInstant
from openfisca_core.periods import Instant, Period
from openfisca_core.populations import Population, GroupPopulation

#: A collection of :obj:`.Entity` or :obj:`.GroupEntity`.
People = Union[Population, GroupPopulation]

#: A callable to get the parameters for the given instant.
Params = Callable[[Instant], ParameterNodeAtInstant]

#: A callable defining a calculation, or a rule, on a system.
Formula = Callable[[People, Period, Params], numpy.ndarray]
