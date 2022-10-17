"""
This file defines variables for the modelled legislation.

A variable is a property of an Entity such as a Person, a Household…

See https://openfisca.org/doc/key-concepts/variables.html
"""

# Import the Entities specifically defined for this tax and benefit system
from policyengine_core.country_template.entities import Household, Person

# Import from openfisca-core the Python objects used to code the legislation in OpenFisca
from policyengine_core.periods import MONTH
from policyengine_core.variables import Variable


class basic_income(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    label = "Basic income provided to adults"
    reference = "https://law.gov.example/basic_income"  # Always use the most official source

    def formula_2016_12(person, period, parameters):
        """
        Basic income provided to adults.

        Since Dec 1st 2016, the basic income is provided to any adult, without considering their income.
        """
        age_condition = (
            person("age", period) >= parameters(period).general.age_of_majority
        )
        return (
            age_condition * parameters(period).benefits.basic_income
        )  # This '*' is a vectorial 'if'. See https://openfisca.org/doc/coding-the-legislation/25_vectorial_computing.html#control-structures

    def formula_2015_12(person, period, parameters):
        """
        Basic income provided to adults.

        From Dec 1st 2015 to Nov 30 2016, the basic income is provided to adults who have no income.
        Before Dec 1st 2015, the basic income does not exist in the law, and calculating it returns its default value, which is 0.
        """
        age_condition = (
            person("age", period) >= parameters(period).general.age_of_majority
        )
        salary_condition = person("salary", period) == 0
        return (
            age_condition
            * salary_condition
            * parameters(period).benefits.basic_income
        )  # The '*' is also used as a vectorial 'and'. See https://openfisca.org/doc/coding-the-legislation/25_vectorial_computing.html#boolean-operations


class housing_allowance(Variable):
    value_type = float
    entity = Household
    definition_period = MONTH
    label = "Housing allowance"
    reference = "https://law.gov.example/housing_allowance"  # Always use the most official source
    end = "2016-11-30"  # This allowance was removed on the 1st of Dec 2016. Calculating it before this date will always return the variable default value, 0.
    unit = "currency-EUR"
    documentation = """
    This allowance was introduced on the 1st of Jan 1980.
    It disappeared in Dec 2016.
    """

    def formula_1980(household, period, parameters):
        """
        Housing allowance.

        This allowance was introduced on the 1st of Jan 1980.
        Calculating it before this date will always return the variable default value, 0.

        To compute this allowance, the 'rent' value must be provided for the same month,
        but 'housing_occupancy_status' is not necessary.
        """
        return (
            household("rent", period)
            * parameters(period).benefits.housing_allowance
        )


# By default, you can use utf-8 characters in a variable. OpenFisca web API manages utf-8 encoding.
class pension(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    label = "Pension for the elderly. Pension attribuée aux personnes âgées. تقاعد."
    reference = [
        "https://fr.wikipedia.org/wiki/Retraite_(économie)",
        "https://ar.wikipedia.org/wiki/تقاعد",
    ]

    def formula(person, period, parameters):
        """
        Pension for the elderly.

        A person's pension depends on their birth date.
        In French: retraite selon l'âge.
        In Arabic: تقاعد.
        """
        age_condition = (
            person("age", period)
            >= parameters(period).general.age_of_retirement
        )
        return age_condition


class parenting_allowance(Variable):
    value_type = float
    entity = Household
    definition_period = MONTH
    label = "Allowance for low income people with children to care for."
    documentation = "Loosely based on the Australian parenting pension."
    reference = "https://www.servicesaustralia.gov.au/individuals/services/centrelink/parenting-payment/who-can-get-it"

    def formula(household, period, parameters):
        """
        Parenting allowance for households.

        A person's parenting allowance depends on how many dependents they have,
        how much they, and their partner, earn
        if they are single with a child under 8
        or if they are partnered with a child under 6.
        """
        parenting_allowance = parameters(period).benefits.parenting_allowance

        household_income = household("household_income", period)
        income_threshold = parenting_allowance.income_threshold
        income_condition = household_income <= income_threshold

        is_single = household.nb_persons(Household.PARENT) == 1
        ages = household.members("age", period)
        under_8 = household.any(ages < 8)
        under_6 = household.any(ages < 6)

        allowance_condition = income_condition * (
            (is_single * under_8) + under_6
        )
        allowance_amount = parenting_allowance.amount

        return allowance_condition * allowance_amount


class household_income(Variable):
    value_type = float
    entity = Household
    definition_period = MONTH
    label = "The sum of the salaries of those living in a household"

    def formula(household, period, _parameters):
        """A household's income."""
        salaries = household.members("salary", period)
        return household.sum(salaries)
