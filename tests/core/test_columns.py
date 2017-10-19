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
    value_type = 'Int'
    entity = Person
    definition_period = MONTH
    label = u"Input variable. No formula."


tax_benefit_system.add_variable(input_variable)


class variable_with_formula(Variable):
    value_type = 'Int'
    entity = Person
    definition_period = MONTH
    label = u"Variable with formula"

    def formula(self, individu, period):
        return self.zeros()


tax_benefit_system.add_variable(variable_with_formula)


# TESTS


def test_is_input_variable():
    variable = tax_benefit_system.variables['input_variable']
    assert variable.is_input_variable()

    variable = tax_benefit_system.variables['variable_with_formula']
    assert not variable.is_input_variable()


def test_attribute_content__formula_class():
    variable = tax_benefit_system.variables['variable_with_formula']
    formula_class = variable.formula

    assert issubclass(formula_class, Formula)
    assert formula_class.__name__ == 'variable_with_formula'

    assert formula_class.dated_formulas_class is not None
    assert type(formula_class.dated_formulas_class) == list
    assert len(formula_class.dated_formulas_class) == 1
    assert type(formula_class.dated_formulas_class[0]) == dict
    assert formula_class.dated_formulas is None

    # CALCULATE
    month = '2005-01'
    simulation = new_simulation(tax_benefit_system, month)
    simulation.calculate('variable_with_formula', month)  # numpy.ndarray

    # No change expected on formula_class after a calculate
    assert formula_class.dated_formulas_class is not None
    assert len(formula_class.dated_formulas_class) == 1
    assert formula_class.dated_formulas is None
