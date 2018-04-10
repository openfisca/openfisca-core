import openfisca_country_template as country_template
from openfisca_country_template.entities import Person

from openfisca_core.model_api import Variable
from openfisca_core.periods import MONTH
from openfisca_core.formulas import Formula


tax_benefit_system = country_template.CountryTaxBenefitSystem()


def new_simulation(tax_benefit_system, month):
    return tax_benefit_system.new_scenario().init_from_attributes(
        period = month,
        input_variables = dict(
            ),
        ).new_simulation()


class input_variable(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = u"Input variable. No formula."


tax_benefit_system.add_variable(input_variable)


class variable_with_formula(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = u"Variable with formula"

    def formula(individu, period):
        return individu.empty_array()


tax_benefit_system.add_variable(variable_with_formula)


# TESTS


def test_is_input_variable():
    variable = tax_benefit_system.variables['input_variable']
    assert variable.is_input_variable()

    variable = tax_benefit_system.variables['variable_with_formula']
    assert not variable.is_input_variable()
