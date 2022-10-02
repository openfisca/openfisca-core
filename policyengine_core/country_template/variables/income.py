"""
This file defines variables for the modelled legislation.

A variable is a property of an Entity such as a Person, a Household…

See https://openfisca.org/doc/key-concepts/variables.html
"""

# Import from openfisca-core the Python objects used to code the legislation in OpenFisca
from policyengine_core.holders import set_input_divide_by_period
from policyengine_core.periods import MONTH
from policyengine_core.variables import Variable

# Import the Entities specifically defined for this tax and benefit system
from policyengine_core.country_template.entities import Person


# This variable is a pure input: it doesn't have a formula
class salary(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    set_input = set_input_divide_by_period  # Optional attribute. Allows user to declare a salary for a year. OpenFisca will spread the yearly amount over the months contained in the year.
    label = "Salary"
    reference = (
        "https://law.gov.example/salary"  # Always use the most official source
    )


class disposable_income(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    label = "Actual amount available to the person at the end of the month"
    reference = "https://stats.gov.example/disposable_income"  # Some variables represent quantities used in economic models, and not defined by law. Always give the source of your definitions.

    def formula(person, period, _parameters):
        """Disposable income."""
        return (
            +person("salary", period)
            + person("basic_income", period)
            - person("income_tax", period)
            - person("social_security_contribution", period)
        )
