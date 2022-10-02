from policyengine_core import periods
from policyengine_core.variables import Variable


class TestVariable(Variable):
    definition_period = periods.ETERNITY
    value_type = float

    def __init__(self, entity):
        self.__class__.entity = entity
        super().__init__()
