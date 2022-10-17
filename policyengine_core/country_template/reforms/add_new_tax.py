"""
This file defines a reform.

A reform is a set of modifications to be applied to a reference tax and benefit system to carry out experiments.

See https://openfisca.org/doc/key-concepts/reforms.html
"""

# Import the Entities specifically defined for this tax and benefit system
from policyengine_core.country_template.entities import Person

# Import from openfisca-core the Python objects used to code the legislation in OpenFisca
from policyengine_core.periods import MONTH
from policyengine_core.reforms import Reform
from policyengine_core.variables import Variable


class has_car(Variable):
    value_type = bool
    entity = Person
    default_value = True
    definition_period = MONTH
    label = "The person has a car"
    reference = "https://law.gov.example/new_tax"  # Always use the most official source


class new_tax(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    label = "New tax"
    reference = "https://law.gov.example/new_tax"  # Always use the most official source

    def formula(person, period, _parameters):
        """
        New tax reform.

        Our reform adds a new variable `new_tax` that is calculated based on
        the current `income_tax`, if the person has a car.
        """
        income_tax = person("income_tax", period)
        has_car = person("has_car", period)

        return (income_tax + 100.0) * has_car


class add_new_tax(Reform):
    def apply(self):
        """
        Apply reform.

        A reform always defines an `apply` method that builds the reformed tax
        and benefit system from the reference one.

        See https://openfisca.org/doc/coding-the-legislation/reforms.html#writing-a-reform
        """
        self.add_variable(has_car)
        self.add_variable(new_tax)
