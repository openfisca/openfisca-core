from policyengine_core.country_template.entities import *
from policyengine_core.model_api import *


class person_id(Variable):
    value_type = int
    entity = Person
    definition_period = ETERNITY
    label = "Person ID"


class household_id(Variable):
    value_type = int
    entity = Household
    definition_period = ETERNITY
    label = "Household ID"


class household_weight(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Household weight"


class person_weight(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Person weight"

    def formula(person, period):
        return person.household("household_weight", period)


class person_household_role(Variable):
    value_type = str
    entity = Person
    definition_period = ETERNITY
    label = "Person household role"


class person_household_id(Variable):
    value_type = int
    entity = Person
    definition_period = ETERNITY
    label = "Person household ID"
