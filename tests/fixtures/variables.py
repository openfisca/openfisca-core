from openfisca_core.periods import DateUnit
from openfisca_core.variables import Variable


class TestVariable(Variable):
    definition_period = DateUnit.ETERNITY
    value_type = float

    def __init__(self, entity):
        self.__class__.entity = entity
        super().__init__()
