# -*- coding: utf-8 -*-

import datetime

from openfisca_core.model_api import Variable
from openfisca_core.periods import MONTH, ETERNITY
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_core.tools import assert_near

import openfisca_country_template as country_template
import openfisca_country_template.situation_examples
from openfisca_country_template.entities import Person

from pytest import fixture, raises, mark

# Check which date is applied whether it comes from Variable attribute (end)
# or formula(s) dates.


tax_benefit_system = country_template.CountryTaxBenefitSystem()


# HELPERS

@fixture
def couple():
    return SimulationBuilder().build_from_entities(tax_benefit_system, openfisca_country_template.situation_examples.couple)


@fixture
def simulation():
    return SimulationBuilder().build_from_entities(tax_benefit_system, openfisca_country_template.situation_examples.single)


def vectorize(individu, number):
    return individu.filled_array(number)


def check_error_at_add_variable(tax_benefit_system, variable, error_message_prefix):
    try:
        tax_benefit_system.add_variable(variable)
    except ValueError as e:
        message = get_message(e)
        if not message or not message.startswith(error_message_prefix):
            raise AssertionError('Incorrect error message. Was expecting something starting by "{}". Got: "{}"'.format(error_message_prefix, message).encode('utf-8'))


def get_message(error):
    return error.args[0].decode()


# TESTS


# NO END ATTRIBUTE - NO DATED FORMULA


class variable__no_date(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = "Variable without date."


def test_before_add__variable__no_date():
    assert tax_benefit_system.variables.get('variable__no_date') is None


def test_variable__no_date():
    tax_benefit_system.add_variable(variable__no_date)
    variable = tax_benefit_system.variables['variable__no_date']
    assert variable.end is None
    assert len(variable.formulas) == 0

# end, no formula


class variable__strange_end_attribute(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = "Variable with dubious end attribute, no formula."
    end = '1989-00-00'


def test_variable__strange_end_attribute():
    try:
        tax_benefit_system.add_variable(variable__strange_end_attribute)

    except ValueError as e:
        message = get_message(e)
        assert message.startswith("Incorrect 'end' attribute format in 'variable__strange_end_attribute'.")

    # Check that Error at variable adding prevents it from registration in the taxbenefitsystem.
    assert not tax_benefit_system.variables.get('variable__strange_end_attribute')


# end, no formula

class variable__end_attribute(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = "Variable with end attribute, no formula."
    end = '1989-12-31'


tax_benefit_system.add_variable(variable__end_attribute)


def test_variable__end_attribute():
    variable = tax_benefit_system.variables['variable__end_attribute']
    assert variable.end == datetime.date(1989, 12, 31)


def test_variable__end_attribute_set_input(simulation):
    month_before_end = '1989-01'
    month_after_end = '1990-01'
    simulation.set_input('variable__end_attribute', month_before_end, 10)
    simulation.set_input('variable__end_attribute', month_after_end, 10)
    assert simulation.calculate('variable__end_attribute', month_before_end) == 10
    assert simulation.calculate('variable__end_attribute', month_after_end) == 0


# end, one formula without date

class end_attribute__one_simple_formula(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = "Variable with end attribute, one formula without date."
    end = '1989-12-31'

    def formula(individu, period):
        return vectorize(individu, 100)


tax_benefit_system.add_variable(end_attribute__one_simple_formula)


def test_formulas_attributes_single_formula():
    formulas = tax_benefit_system.variables['end_attribute__one_simple_formula'].formulas
    assert formulas['0001-01-01'] is not None


def test_call__end_attribute__one_simple_formula(simulation):
    month = '1979-12'
    assert simulation.calculate('end_attribute__one_simple_formula', month) == 100

    month = '1989-12'
    assert simulation.calculate('end_attribute__one_simple_formula', month) == 100

    month = '1990-01'
    assert simulation.calculate('end_attribute__one_simple_formula', month) == 0


def test_dates__end_attribute__one_simple_formula():
    variable = tax_benefit_system.variables['end_attribute__one_simple_formula']
    assert variable.end == datetime.date(1989, 12, 31)

    assert len(variable.formulas) == 1
    assert variable.formulas.keys()[0] == str(datetime.date.min)


# NO END ATTRIBUTE - DATED FORMULA(S)


# formula, strange name

class no_end_attribute__one_formula__strange_name(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = "Variable without end attribute, one stangely named formula."

    def formula_2015_toto(individu, period):
        return vectorize(individu, 100)


def test_add__no_end_attribute__one_formula__strange_name():
    check_error_at_add_variable(tax_benefit_system, no_end_attribute__one_formula__strange_name,
    'Unrecognized formula name in variable "no_end_attribute__one_formula__strange_name". Expecting "formula_YYYY" or "formula_YYYY_MM" or "formula_YYYY_MM_DD where YYYY, MM and DD are year, month and day. Found: ')


# formula, start

class no_end_attribute__one_formula__start(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = "Variable without end attribute, one dated formula."

    def formula_2000_01_01(individu, period):
        return vectorize(individu, 100)


tax_benefit_system.add_variable(no_end_attribute__one_formula__start)


def test_call__no_end_attribute__one_formula__start(simulation):
    month = '1999-12'
    assert simulation.calculate('no_end_attribute__one_formula__start', month) == 0

    month = '2000-05'
    assert simulation.calculate('no_end_attribute__one_formula__start', month) == 100

    month = '2020-01'
    assert simulation.calculate('no_end_attribute__one_formula__start', month) == 100


def test_dates__no_end_attribute__one_formula__start():
    variable = tax_benefit_system.variables['no_end_attribute__one_formula__start']
    assert variable.end is None

    assert len(variable.formulas) == 1
    assert variable.formulas.keys()[0] == '2000-01-01'


class no_end_attribute__one_formula__eternity(Variable):
    value_type = int
    entity = Person
    definition_period = ETERNITY  # For this entity, this variable shouldn't evolve through time
    label = "Variable without end attribute, one dated formula."

    def formula_2000_01_01(individu, period):
        return vectorize(individu, 100)


tax_benefit_system.add_variable(no_end_attribute__one_formula__eternity)


@mark.xfail()
def test_call__no_end_attribute__one_formula__eternity(simulation):
    month = '1999-12'
    assert simulation.calculate('no_end_attribute__one_formula__eternity', month) == 0

    # This fails because a definition period of "ETERNITY" caches for all periods
    month = '2000-01'
    assert simulation.calculate('no_end_attribute__one_formula__eternity', month) == 100


def test_call__no_end_attribute__one_formula__eternity_before(simulation):
    month = '1999-12'
    assert simulation.calculate('no_end_attribute__one_formula__eternity', month) == 0


def test_call__no_end_attribute__one_formula__eternity_after(simulation):
    month = '2000-01'
    assert simulation.calculate('no_end_attribute__one_formula__eternity', month) == 100


# formula, different start formats


class no_end_attribute__formulas__start_formats(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = "Variable without end attribute, multiple dated formulas."

    def formula_2000(individu, period):
        return vectorize(individu, 100)

    def formula_2010_01(individu, period):
        return vectorize(individu, 200)


tax_benefit_system.add_variable(no_end_attribute__formulas__start_formats)


def test_formulas_attributes_dated_formulas():
    formulas = tax_benefit_system.variables['no_end_attribute__formulas__start_formats'].formulas
    assert(len(formulas) == 2)
    assert formulas['2000-01-01'] is not None
    assert formulas['2010-01-01'] is not None


def test_get_formulas():
    variable = tax_benefit_system.variables['no_end_attribute__formulas__start_formats']
    formula_2000 = variable.formulas['2000-01-01']
    formula_2010 = variable.formulas['2010-01-01']

    assert variable.get_formula('1999-01') is None
    assert variable.get_formula('2000-01') == formula_2000
    assert variable.get_formula('2009-12') == formula_2000
    assert variable.get_formula('2009-12-31') == formula_2000
    assert variable.get_formula('2010-01') == formula_2010
    assert variable.get_formula('2010-01-01') == formula_2010


def test_call__no_end_attribute__formulas__start_formats(simulation):
    month = '1999-12'
    assert simulation.calculate('no_end_attribute__formulas__start_formats', month) == 0

    month = '2000-01'
    assert simulation.calculate('no_end_attribute__formulas__start_formats', month) == 100

    month = '2009-12'
    assert simulation.calculate('no_end_attribute__formulas__start_formats', month) == 100

    month = '2010-01'
    assert simulation.calculate('no_end_attribute__formulas__start_formats', month) == 200


# Multiple formulas, different names with date overlap

class no_attribute__formulas__different_names__dates_overlap(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = "Variable, no end attribute, multiple dated formulas with different names but same dates."

    def formula_2000(individu, period):
        return vectorize(individu, 100)

    def formula_2000_01_01(individu, period):
        return vectorize(individu, 200)


def test_add__no_attribute__formulas__different_names__dates_overlap():
    # Variable isn't registered in the taxbenefitsystem
    check_error_at_add_variable(tax_benefit_system, no_attribute__formulas__different_names__dates_overlap, "Dated formulas overlap")


# formula(start), different names, no date overlap

class no_attribute__formulas__different_names__no_overlap(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = "Variable, no end attribute, multiple dated formulas with different names and no date overlap."

    def formula_2000_01_01(individu, period):
        return vectorize(individu, 100)

    def formula_2010_01_01(individu, period):
        return vectorize(individu, 200)


tax_benefit_system.add_variable(no_attribute__formulas__different_names__no_overlap)


def test_call__no_attribute__formulas__different_names__no_overlap(simulation):
    month = '2009-12'
    assert simulation.calculate('no_attribute__formulas__different_names__no_overlap', month) == 100

    month = '2015-05'
    assert simulation.calculate('no_attribute__formulas__different_names__no_overlap', month) == 200


# END ATTRIBUTE - DATED FORMULA(S)


# formula, start.

class end_attribute__one_formula__start(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = "Variable with end attribute, one dated formula."
    end = '2001-12-31'

    def formula_2000_01_01(individu, period):
        return vectorize(individu, 100)


tax_benefit_system.add_variable(end_attribute__one_formula__start)


def test_call__end_attribute__one_formula__start(simulation):
    month = '1980-01'
    assert simulation.calculate('end_attribute__one_formula__start', month) == 0

    month = '2000-01'
    assert simulation.calculate('end_attribute__one_formula__start', month) == 100

    month = '2002-01'
    assert simulation.calculate('end_attribute__one_formula__start', month) == 0


# end < formula, start.

class stop_attribute_before__one_formula__start(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = "Variable with stop attribute only coming before formula start."
    end = '1990-01-01'

    def formula_2000_01_01(individu, period):
        return vectorize(individu, 0)


def test_add__stop_attribute_before__one_formula__start():
    check_error_at_add_variable(tax_benefit_system, stop_attribute_before__one_formula__start, 'You declared that "stop_attribute_before__one_formula__start" ends on "1990-01-01", but you wrote a formula to calculate it from "2000-01-01"')


# end, formula with dates intervals overlap.

class end_attribute_restrictive__one_formula(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = "Variable with end attribute, one dated formula and dates intervals overlap."
    end = '2001-01-01'

    def formula_2001_01_01(individu, period):
        return vectorize(individu, 100)


tax_benefit_system.add_variable(end_attribute_restrictive__one_formula)


def test_call__end_attribute_restrictive__one_formula(simulation):
    month = '2000-12'
    assert simulation.calculate('end_attribute_restrictive__one_formula', month) == 0

    month = '2001-01'
    assert simulation.calculate('end_attribute_restrictive__one_formula', month) == 100

    month = '2000-05'
    assert simulation.calculate('end_attribute_restrictive__one_formula', month) == 0


# formulas of different names (without dates overlap on formulas)

class end_attribute__formulas__different_names(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = "Variable with end attribute, multiple dated formulas with different names."
    end = '2010-12-31'

    def formula_2000_01_01(individu, period):
        return vectorize(individu, 100)

    def formula_2005_01_01(individu, period):
        return vectorize(individu, 200)

    def formula_2010_01_01(individu, period):
        return vectorize(individu, 300)


tax_benefit_system.add_variable(end_attribute__formulas__different_names)


def test_call__end_attribute__formulas__different_names(simulation):
    month = '2000-01'
    assert simulation.calculate('end_attribute__formulas__different_names', month) == 100

    month = '2005-01'
    assert simulation.calculate('end_attribute__formulas__different_names', month) == 200

    month = '2010-12'
    assert simulation.calculate('end_attribute__formulas__different_names', month) == 300


def test_get_formula(simulation):
    person = simulation.person
    disposable_income_formula = tax_benefit_system.get_variable('disposable_income').get_formula()
    disposable_income = person('disposable_income', '2017-01')
    disposable_income_2 = disposable_income_formula(person, '2017-01', None)  # No need for parameters here

    assert_near(disposable_income, disposable_income_2)


def test_unexpected_attr():
    class variable_with_strange_attr(Variable):
        value_type = int
        entity = Person
        definition_period = MONTH
        unexpected = '???'

    with raises(ValueError):
        tax_benefit_system.add_variable(variable_with_strange_attr)
