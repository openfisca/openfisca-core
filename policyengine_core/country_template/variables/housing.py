"""
This file defines variables for the modelled legislation.

A variable is a property of an Entity such as a Person, a Household…

See https://openfisca.org/doc/key-concepts/variables.html
"""

# Import from openfisca-core the Python objects used to code the legislation in OpenFisca
from policyengine_core.enums import Enum
from policyengine_core.periods import MONTH
from policyengine_core.variables import Variable

# Import the Entities specifically defined for this tax and benefit system
from policyengine_core.country_template.entities import Household


# This variable is a pure input: it doesn't have a formula
class accommodation_size(Variable):
    value_type = float
    entity = Household
    definition_period = MONTH
    label = "Size of the accommodation, in square metres"


# This variable is a pure input: it doesn't have a formula
class rent(Variable):
    value_type = float
    entity = Household
    definition_period = MONTH
    label = "Rent paid by the household"


# Possible values for the housing_occupancy_status variable, defined further down
# See more at <https://openfisca.org/doc/coding-the-legislation/20_input_variables.html#advanced-example-enumerations-enum>
class HousingOccupancyStatus(Enum):
    __order__ = "owner tenant free_lodger homeless"
    owner = "Owner"
    tenant = "Tenant"
    free_lodger = "Free lodger"
    homeless = "Homeless"


class housing_occupancy_status(Variable):
    value_type = Enum
    possible_values = HousingOccupancyStatus
    default_value = HousingOccupancyStatus.tenant
    entity = Household
    definition_period = MONTH
    label = "Legal housing situation of the household concerning their main residence"


class postal_code(Variable):
    value_type = str
    max_length = 5
    entity = Household
    definition_period = MONTH
    label = "Postal code of the household"
