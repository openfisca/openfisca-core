# -*- coding: utf-8 -*-

import datetime

from openfisca_core.model_api import Variable
from openfisca_core.taxbenefitsystems import VariableNotFound
from openfisca_core.periods import MONTH, ETERNITY
from openfisca_core.columns import IntCol

import openfisca_dummy_country as dummy_country
from openfisca_dummy_country.entities import Individu

# Check which date is applied whether it comes from Variable attribute (end)
# or formula(s) dates.


tax_benefit_system = dummy_country.DummyTaxBenefitSystem()


# HELPERS


def new_simulation(tax_benefit_system, month):
    return tax_benefit_system.new_scenario().init_single_entity(
        period = month,
        parent1 = dict(
            ),
        ).new_simulation()


def vectorize(function, number):
    return (function.zeros() + 1) * number


def check_error_at_add_variable(tax_benefit_system, variable, assertion_message_prefix):
    try:
        tax_benefit_system.add_variable(variable)
    except AssertionError, e:
        if hasattr(e, 'message'):
            message = getattr(e, 'message')
            assert message.startswith(assertion_message_prefix), message
        else:
            raise
    except:
        raise


# TESTS


# NO DATED ATTRIBUTE(S) - NO DATED FORMULA


class variable__no_dated_attributes(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable without date."


tax_benefit_system.add_variable(variable__no_dated_attributes)


def test_variable__no_dated_attributes():
    variable = tax_benefit_system.column_by_name['variable__no_dated_attributes']
    assert variable is not None
    assert variable.end is None
    assert variable.formula_class.dated_formulas_class.__len__() == 0


# DATED ATTRIBUTE(S) - NO DATED FORMULA


class variable__deprecated_start_date(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with dated attributes (including deprecated start_date), no function."
    start_date = datetime.date(1980, 1, 1)  # Deprecated
    end = '1989-12-31'


check_error_at_add_variable(tax_benefit_system, variable__deprecated_start_date, 'Deprecated "start_date" attribute in definition of variable')


# end, no function

class variable__strange_end_attribute(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with dubious end attribute, no function."
    end = '1989-00-00'


def test_variable__strange_end_attribute():
    try:
        tax_benefit_system.add_variable(variable__strange_end_attribute)

    except ValueError, e:
        if hasattr(e, 'message'):
            message = getattr(e, 'message')
            assert message.startswith("Incorrect 'end' attribute format"), message
    except:
        raise

    # Check that Error at variable adding prevents it from registration in the taxbenefitsystem.
    assert not hasattr(tax_benefit_system.column_by_name, "variable__strange_end_attribute")


# end, no function

class variable__dated_attribute(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with end attribute, no function."
    end = '1989-12-31'


tax_benefit_system.add_variable(variable__dated_attribute)


def test_variable__dated_attribute():
    variable = tax_benefit_system.column_by_name['variable__dated_attribute']
    assert variable is not None
    assert variable.end == '1989-12-31'


# end, one function without date

class dated_attribute__one_formula(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with end attribute, one function without date."
    end = '1989-12-31'

    def formula(self, individu, period, nb):
        return vectorize(self, nb)


tax_benefit_system.add_variable(dated_attribute__one_formula)


def test_call__dated_attribute__one_formula():
    month = '1979-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attribute__one_formula', month, extra_params=[100]) == 100

    month = '1989-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attribute__one_formula', month, extra_params=[100]) == 100

    month = '1990-01'
    simulation = new_simulation(tax_benefit_system, month)
    result = simulation.calculate('dated_attribute__one_formula', month, extra_params=[100])
    assert result == IntCol.default, result


def test_dates__dated_attribute__one_formula():
    variable = tax_benefit_system.column_by_name['dated_attribute__one_formula']
    assert variable is not None
    assert variable.end == '1989-12-31'

    assert variable.formula_class.dated_formulas_class.__len__() == 1
    formula = variable.formula_class.dated_formulas_class[0]
    assert formula is not None
    assert formula['start_instant'].date == datetime.date.min


# NO DATED ATTRIBUTE - DATED FORMULA(S)


# function, start

class no_attributes__one_formula__start(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable without end attribute, one dated function."

    def formula_2000_01_01(self, individu, period, nb):
        return vectorize(self, nb)


tax_benefit_system.add_variable(no_attributes__one_formula__start)


def test_call__no_attributes__one_formula__start():
    month = '1999-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attributes__one_formula__start', month, extra_params=[100]) == IntCol.default

    month = '2000-05'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attributes__one_formula__start', month, extra_params=[100]) == 100

    month = '2020-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attributes__one_formula__start', month, extra_params=[100]) == 100


def test_dates__no_attributes__one_formula__start():
    variable = tax_benefit_system.column_by_name['no_attributes__one_formula__start']
    assert variable is not None
    assert variable.end is None

    assert variable.formula_class.dated_formulas_class.__len__() == 1
    formula = variable.formula_class.dated_formulas_class[0]
    assert formula is not None

    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2000, 1, 1)


class no_attributes__one_formula__eternity(Variable):
    column = IntCol
    entity = Individu
    definition_period = ETERNITY  # For this entity, this variable shouldn't evolve through time
    label = u"Variable without end attribute, one dated function."

    def formula_2000_01_01(self, individu, period, nb):
        return vectorize(self, nb)


tax_benefit_system.add_variable(no_attributes__one_formula__eternity)


def test_call__no_attributes__one_formula__eternity():
    month = '1999-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attributes__one_formula__eternity', month, extra_params=[100]) == IntCol.default

    month = '2000-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attributes__one_formula__eternity', month, extra_params=[100]) == 100


# function, different start formats

class no_attributes__formulas__start_formats(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable without end attribute, multiple dated functions."

    def formula_2000(self, individu, period):
        return vectorize(self, 100)

    def formula_2010_01(self, individu, period):
        return vectorize(self, 200)


tax_benefit_system.add_variable(no_attributes__formulas__start_formats)


def test_call__no_attributes__formulas__start_formats():
    month = '1999-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attributes__formulas__start_formats', month) == IntCol.default

    month = '2000-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attributes__formulas__start_formats', month) == 100

    month = '2009-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attributes__formulas__start_formats', month) == 100

    month = '2010-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attributes__formulas__start_formats', month) == 200


def test_dates__no_attributes__formulas__start_formats():
    variable = tax_benefit_system.column_by_name['no_attributes__formulas__start_formats']
    assert variable is not None
    assert variable.end is None

    assert variable.formula_class.dated_formulas_class.__len__() == 2

    i = 0
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2000, 1, 1)

    i = 1
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2010, 1, 1)


# Multiple functions, different names with date overlap

class no_attribute__formulas__different_names__dates_overlap(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable, no dated attribute, multiple dated functions with different names but same dates."

    def formula_2000(self, individu, period):
        return vectorize(self, 100)

    def formula_2000_01_01(self, individu, period):
        return vectorize(self, 200)


def test_add__no_attribute__formulas__different_names__dates_overlap():
    # Variable isn't registered in the taxbenefitsystem
    check_error_at_add_variable(tax_benefit_system, no_attribute__formulas__different_names__dates_overlap, "Dated formulas overlap")


# function(start), different names, no date overlap

class no_attribute__formulas__different_name__no_overlap(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable, no and attribute, multiple dated functions with different names and no date overlap."

    def formula_2000_01_01(self, individu, period):
        return vectorize(self, 100)

    def formula_2010_01_01(self, individu, period):
        return vectorize(self, 200)


tax_benefit_system.add_variable(no_attribute__formulas__different_name__no_overlap)


def test_call__no_attribute__formulas__different_name__no_overlap():
    month = '2009-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attribute__formulas__different_name__no_overlap', month) == 100

    month = '2015-05'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attribute__formulas__different_name__no_overlap', month) == 200


def test_dates__no_attribute__formulas__different_name__no_overlap():
    variable = tax_benefit_system.column_by_name['no_attribute__formulas__different_name__no_overlap']
    assert variable is not None

    assert variable.formula_class.dated_formulas_class.__len__() == 2

    i = 0
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2000, 1, 1)

    i = 1
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2010, 1, 1)


# DATED ATTRIBUTE - DATED FORMULA(S)


# function, start.

class dated_attribute__one_formula__start(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with end attribute, one dated function."
    end = '2001-12-31'

    def formula_2000_01_01(self, individu, period, nb):
        return vectorize(self, nb)


tax_benefit_system.add_variable(dated_attribute__one_formula__start)


def test_call__dated_attribute__one_formula__start():
    month = '1980-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attribute__one_formula__start', month, extra_params=[100]) == IntCol.default

    month = '2000-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attribute__one_formula__start', month, extra_params=[100]) == 100

    month = '2002-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attribute__one_formula__start', month, extra_params=[100]) == IntCol.default


# end < function, start.

class stop_attribute_before__one_formula__start(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with stop attribute only coming before formula start."
    end = '1990-01-01'

    def formula_2000_01_01(self, individu, period, nb):
        return vectorize(self, nb)


def test_add__stop_attribute_before__one_formula__start():
    check_error_at_add_variable(tax_benefit_system, 'stop_attribute_before__one_formula__start', 'end date before formula start')


# end, function with dates intervals overlap.

class dated_attribute_restrictive__one_formula(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with dated attributes, one dated function and dates intervals overlap."
    end = '2001-01-01'

    def formula_2001_01_01(self, individu, period, nb):
        return vectorize(self, nb)


tax_benefit_system.add_variable(dated_attribute_restrictive__one_formula)


def test_call__dated_attribute_restrictive__one_formula():
    month = '2000-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attribute_restrictive__one_formula', month, extra_params=[100]) == IntCol.default

    month = '2001-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attribute_restrictive__one_formula', month, extra_params=[100]) == 100

    month = '2000-05'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attribute_restrictive__one_formula', month, extra_params=[100]) == IntCol.default


# end, functions different names (without dates overlap on functions)

class dated_attribute__formulas__different_names(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with end attribute, multiple dated functions with different names."
    end = '2005-12-31'

    def formula_2000_01_01(self, individu, period):
        return vectorize(self, 100)

    def formula_2010_01_01(self, individu, period):
        return vectorize(self, 200)


def test_add__dated_attribute__formulas__different_names():
    check_error_at_add_variable(tax_benefit_system, 'dated_attribute__formulas__different_names', 'end date before xxx formula start')
