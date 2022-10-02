"""
This file defines variables for the modelled legislation.

A variable is a property of an Entity such as a Person, a Household…

See https://openfisca.org/doc/key-concepts/variables.html
"""

from datetime import date

# Import from numpy the operations you need to apply on OpenFisca's population vectors
# Import from openfisca-core the Python objects used to code the legislation in OpenFisca
from numpy import where
from policyengine_core.periods import ETERNITY, MONTH
from policyengine_core.variables import Variable

# Import the Entities specifically defined for this tax and benefit system
from policyengine_core.country_template.entities import Person


# This variable is a pure input: it doesn't have a formula
class birth(Variable):
    value_type = date
    default_value = date(
        1970, 1, 1
    )  # By default, if no value is set for a simulation, we consider the people involved in a simulation to be born on the 1st of Jan 1970.
    entity = Person
    label = "Birth date"
    definition_period = ETERNITY  # This variable cannot change over time.
    reference = "https://en.wiktionary.org/wiki/birthdate"


class age(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = "Person's age (in years)"

    def formula(person, period, _parameters):
        """
        Person's age (in years).

        A person's age is computed according to its birth date.
        """
        birth = person("birth", period)
        birth_year = birth.astype("datetime64[Y]").astype(int) + 1970
        birth_month = birth.astype("datetime64[M]").astype(int) % 12 + 1
        birth_day = (birth - birth.astype("datetime64[M]") + 1).astype(int)

        is_birthday_past = (birth_month < period.start.month) + (
            birth_month == period.start.month
        ) * (birth_day <= period.start.day)

        return (period.start.year - birth_year) - where(
            is_birthday_past, 0, 1
        )  # If the birthday is not passed this year, subtract one year
