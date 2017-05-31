# -*- coding: utf-8 -*-

import datetime
from nose.tools import raises

from openfisca_core.model_api import Variable
from openfisca_core.taxbenefitsystems import VariableNotFound
from openfisca_core.periods import MONTH
from openfisca_core.columns import IntCol

import openfisca_dummy_country as dummy_country
from openfisca_dummy_country.entities import Individu

# Check which date is applied whether it comes from Variable attribute (stop_date)
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


def has_dated_attribute(variable):
    return variable.end is not None


def add_variable_catch_assertion(tax_benefit_system, variable, assertion_message_prefix):
    try:
        tax_benefit_system.add_variable(variable)
    except AssertionError, e:
        if hasattr(e, 'message'):
            assert getattr(e, 'message').startswith(assertion_message_prefix)
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
    label = u"Variable with dated attributes, no function."
    start_date = datetime.date(1980, 1, 1)  # Deprecated
    stop_date = datetime.date(1989, 12, 31)


add_variable_catch_assertion(tax_benefit_system, variable__deprecated_start_date, 'Deprecated "start_date" attribute in definition of variable')


# 371 - stop_date, no function

class variable__dated_attributes(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with dated attributes, no function."
    # start_date = datetime.date(1980, 1, 1)
    stop_date = datetime.date(1989, 12, 31)


tax_benefit_system.add_variable(variable__dated_attributes)


def test_variable__dated_attributes():
    variable = tax_benefit_system.column_by_name['variable__dated_attributes']
    assert variable is not None
    assert variable.end == datetime.date(1989, 12, 31)
    assert variable.formula_class.dated_formulas_class.__len__() == 0


# 371 - stop_date, one function without date

class dated_attributes__one_formula(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with dated attributes, one function without date."
    # start_date = datetime.date(1980, 1, 1)
    stop_date = datetime.date(1989, 12, 31)

    def formula(self, individu, period, nb):
        return vectorize(self, nb)


tax_benefit_system.add_variable(dated_attributes__one_formula)


def test_call__dated_attributes__one_formula():
    month = '1979-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__one_formula', month, extra_params=[100]) == 100

    month = '1983-05'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__one_formula', month, extra_params=[100]) == 100

    month = '1990-01'
    simulation = new_simulation(tax_benefit_system, month)
    result = simulation.calculate('dated_attributes__one_formula', month, extra_params=[100])
    assert result == IntCol.default, result


def test_dates__dated_attributes__one_formula():
    variable = tax_benefit_system.column_by_name['dated_attributes__one_formula']
    assert variable is not None
    assert variable.end == datetime.date(1989, 12, 31)

    assert variable.formula_class.dated_formulas_class.__len__() == 1
    formula = variable.formula_class.dated_formulas_class[0]
    assert formula is not None


# NO DATED ATTRIBUTE - DATED FORMULA(S)


# 371 - function, start only

class no_attributes__one_formula__start_only(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable without dated attributes, one decorated function, start only."

    def formula_2000_01_01(self, individu, period, nb):
        return vectorize(self, nb)


tax_benefit_system.add_variable(no_attributes__one_formula__start_only)


def test_call__no_attributes__one_formula__start_only():
    month = '1999-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attributes__one_formula__start_only', month, extra_params=[100]) == IntCol.default

    month = '2000-05'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attributes__one_formula__start_only', month, extra_params=[100]) == 100

    month = '2020-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attributes__one_formula__start_only', month, extra_params=[100]) == 100


def test_dates__no_attributes__one_formula__start_only():
    variable = tax_benefit_system.column_by_name['no_attributes__one_formula__start_only']
    assert variable is not None

    # Check that attributes' dates aren't modified by formula dates
    assert not has_dated_attribute(variable)

    assert variable.formula_class.dated_formulas_class.__len__() == 1
    formula = variable.formula_class.dated_formulas_class[0]
    assert formula is not None

    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2000, 1, 1)


# 371 - function, stop only

class no_attributes__one_formula__stop_date(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable, no dated attributes, one decorated function, stop only."
    stop_date = datetime.date(2009, 12, 31)

    def formula(self, individu, period, nb):
        return vectorize(self, nb)

tax_benefit_system.add_variable(no_attributes__one_formula__stop_date)


def test_add__no_attributes__one_formula__stop_date():
    month = '2008-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attributes__one_formula__stop_date', month, extra_params=[100]) == 100

    month = '2015-05'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attributes__one_formula__stop_date', month, extra_params=[100]) == IntCol.default


# 371 - Multiple functions, different names with date overlap

class no_attributes__formulas__different_names__dates_overlap(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable, no dated attributes, multiple fully decorated functions with different names but same dates."

    def formula_2000(self, individu, period):
        return vectorize(self, 100)

    def formula_2000_01_01(self, individu, period):
        return vectorize(self, 200)


add_variable_catch_assertion(tax_benefit_system, no_attributes__formulas__different_names__dates_overlap, "Dated formulas overlap")


def test_call__no_attributes__formulas__different_names__dates_overlap():
    month = '2005-05'
    simulation = new_simulation(tax_benefit_system, month)
    try:
        simulation.calculate('no_attributes__formulas__different_names__dates_overlap', month)
    except VariableNotFound, e:
        assert getattr(e, 'message').startswith("You tried to calculate or to set a value for variable")
    except:
        raise


def test_dates__no_attributes__formulas__different_names__dates_overlap():
    # Check that AssertionError at variable adding prevents it from registration in the taxbenefitsystem.
    assert not hasattr(tax_benefit_system.column_by_name, "no_attributes__formulas__different_names__dates_overlap")


# 371 - function(start), different names, no date overlap

class no_attributes__formulas__different_name__no_overlap(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable, no dated attributes, multiple decorated functions with different names and no date overlap."

    def formula_2000_01_01(self, individu, period):
        return vectorize(self, 100)

    def formula_2010_01_01(self, individu, period):
        return vectorize(self, 200)


tax_benefit_system.add_variable(no_attributes__formulas__different_name__no_overlap)


def test_call__no_attributes__formulas__different_name__no_overlap():
    # Check that only last declared function is registered.
    month = '2009-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attributes__formulas__different_name__no_overlap', month) == 100

    month = '2015-05'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attributes__formulas__different_name__no_overlap', month) == 200


def test_dates__no_attributes__formulas__different_name__no_overlap():
    # Check that only last declared function is registered.
    variable = tax_benefit_system.column_by_name['no_attributes__formulas__different_name__no_overlap']
    assert variable is not None
    assert not has_dated_attribute(variable)

    assert variable.formula_class.dated_formulas_class.__len__() == 2

    # TODO compare dated_formulas_class and dated_formulas 

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


# DATED ATTRIBUTE(S) - DATED FORMULA(S)


# 371 - function, start only.

class dated_attributes__one_formula__start_only(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with dated attributes, one decorated function, start only."
    # start_date = datetime.date(1980, 1, 1)
    stop_date = datetime.date(2001, 12, 31)

    def formula_2000_01_01(self, individu, period, nb):
        return vectorize(self, nb)


tax_benefit_system.add_variable(dated_attributes__one_formula__start_only)


def test_call__dated_attributes__one_formula__start_only():
    month = '1980-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__one_formula__start_only', month, extra_params=[100]) == IntCol.default

    month = '2000-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__one_formula__start_only', month, extra_params=[100]) == 100

    month = '2002-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__one_formula__start_only', month, extra_params=[100]) == IntCol.default


def test_dates__dated_attributes__one_formula__start_only():
    variable = tax_benefit_system.column_by_name['dated_attributes__one_formula__start_only']
    assert variable is not None
    assert has_dated_attribute(variable)
    assert variable.end == datetime.date(2001, 12, 31)

    assert variable.formula_class.dated_formulas_class.__len__() == 1
    formula = variable.formula_class.dated_formulas_class[0]
    assert formula is not None

    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2000, 1, 1)


# 371 - stop_date < function, start.

class stop_attribute_before__one_formula__start(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with stop attribute only coming before formula start."
    stop_date = datetime.date(1990, 1, 1)

    def formula_2000_01_01(self, individu, period, nb):
        return vectorize(self, nb)


tax_benefit_system.add_variable(stop_attribute_before__one_formula__start)


def test_call__stop_attribute_before__one_formula__start():
    # Check that as attribute start date is after formula's start, attribute start wins. >> the most restrictive wins.
    month = '1989-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('stop_attribute_before__one_formula__start', month, extra_params=[100]) == IntCol.default

    month = '2000-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('stop_attribute_before__one_formula__start', month, extra_params=[100]) == IntCol.default


def test_dates__stop_attribute_before__one_formula__start():
    variable = tax_benefit_system.column_by_name['stop_attribute_before__one_formula__start']
    assert variable is not None
    assert variable.end == datetime.date(1990, 1, 1)

    assert variable.formula_class.dated_formulas_class.__len__() == 1
    formula = variable.formula_class.dated_formulas_class[0]
    assert formula is not None

    # Check that formula's start_instant is unchanged (it doesn't get variable.end attribute even if it's older).
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2000, 1, 1)


# 371 - stop_date, function with dates intervals overlap.

class dated_attributes_restrictive__one_formula(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with dated attributes, one fully decorated function and dates intervals overlap."
    # start_date = datetime.date(1980, 1, 1)
    stop_date = datetime.date(2001, 12, 31)

    def formula_2000_01_01(self, individu, period, nb):
        return vectorize(self, nb)


tax_benefit_system.add_variable(dated_attributes_restrictive__one_formula)


def test_call__dated_attributes_restrictive__one_formula():
    month = '1979-12'  # Older than most restrictive start.
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes_restrictive__one_formula', month, extra_params=[100]) == IntCol.default

    month = '1999-12'  # Between attribute start and formula start.
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes_restrictive__one_formula', month, extra_params=[100]) == IntCol.default

    month = '2001-12'  # Inside most restrictive start and stop interval.
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes_restrictive__one_formula', month, extra_params=[100]) == 100

    month = '2009-12'  # Between attribute stop and formula stop.
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes_restrictive__one_formula', month, extra_params=[100]) == IntCol.default


def test_dates__dated_attributes_restrictive__one_formula():
    variable = tax_benefit_system.column_by_name['dated_attributes_restrictive__one_formula']
    assert variable is not None
    assert variable.end == datetime.date(2001, 12, 31)

    assert variable.formula_class.dated_formulas_class.__len__() == 1
    formula = variable.formula_class.dated_formulas_class[0]
    assert formula is not None

    # Check that formula's dates get most restrictive dates among attributes' dates and formula's dates.
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2000, 1, 1)


# 371 - stop_date, functions different names (without dates overlap on functions)

class dated_attributes__formulas__different_names(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with dated attributes, multiple fully decorated functions with different names."
    # start_date = datetime.date(1980, 1, 1)
    stop_date = datetime.date(2005, 12, 31)

    def formula_2000_01_01(self, individu, period):
        return vectorize(self, 100)

    def formula_2010_01_01(self, individu, period):
        return vectorize(self, 200)


tax_benefit_system.add_variable(dated_attributes__formulas__different_names)


def test_call__dated_attributes__formulas__different_names():
    month = '1979-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__formulas__different_names', month) == IntCol.default

    month = '1999-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__formulas__different_names', month) == IntCol.default

    month = '2005-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__formulas__different_names', month) == 100

    month = '2015-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__formulas__different_names', month) == IntCol.default


def test_dates__dated_attributes__formulas__different_names():
    dated_function_nb = 2
    variable = tax_benefit_system.column_by_name['dated_attributes__formulas__different_names']
    assert variable is not None
    assert has_dated_attribute(variable)
    assert variable.end == datetime.date(2005, 12, 31)

    assert variable.formula_class.dated_formulas_class.__len__() == dated_function_nb

    # ERROR? Overlap between attribute dates and 1st function dates
    # BUT 1st function dates are unchanged.
    i = 0
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2000, 1, 1)

    # ERROR? No overlap between attributes dates and 2nd function dates
    # BUT last declared function dates get most restrictive stop date.
    i = 1
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2010, 1, 1)


# 371 - function start_instant > stop_date

class dated_attributes__inactive_formulas(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with restrictive dated attribute, more than 2 fully decorated functions, all outside dated attributes interval."
    # start_date = datetime.date(1980, 1, 1)
    stop_date = datetime.date(1990, 12, 31)

    def formula_2000_01_01(self, individu, period):
        return vectorize(self, 100)

    def formula_2006_01_01(self, individu, period):
        return vectorize(self, 200)

    def formula_2011_01_01(self, individu, period):
        return vectorize(self, 300)

    def formula_2016_01_01(self, individu, period):
        return vectorize(self, 400)


tax_benefit_system.add_variable(dated_attributes__inactive_formulas)


def test_call__dated_attributes__inactive_formulas():
    month = '1985-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__inactive_formulas', month) == IntCol.default

    month = '2000-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__inactive_formulas', month) == IntCol.default  # Raises an error before DatedVariable update.

    month = '2006-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__inactive_formulas', month) == IntCol.default  # Raises an error before DatedVariable update.

    month = '2011-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__inactive_formulas', month) == IntCol.default  # Raises an error before DatedVariable update.

    month = '2016-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__inactive_formulas', month) == IntCol.default


def test_dates__dated_attributes__inactive_formulas():
    dated_function_nb = 4

    variable = tax_benefit_system.column_by_name['dated_attributes__inactive_formulas']
    assert variable is not None
    assert has_dated_attribute(variable)
    assert variable.end == datetime.date(1990, 12, 31)

    # Even inactivated functions (functions with start date < attribute stop date) should be registered.
    assert variable.formula_class.dated_formulas_class.__len__() == dated_function_nb

    i = 0
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None
    # Raises an error before DatedVariable update.
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2000, 1, 1)

    i = 1
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None
    # Raises an error before DatedVariable update.
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2006, 1, 1)

    i = 2
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None
    # Raises an error before DatedVariable update.
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2011, 1, 1)

    i = 3
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None
    # Raises an error before DatedVariable update.
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2016, 1, 1)




# 371 - stop_date, all functions start_instant < stop_date

class dated_attributes__active_formulas(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with dated attributes, more than 2 fully decorated functions, all inside dated attributes interval."
    # start_date = datetime.date(2000, 1, 1)
    stop_date = datetime.date(2020, 12, 31)

    def formula_2000_01_01(self, individu, period):
        return vectorize(self, 100)

    def formula_2006_01_01(self, individu, period):
        return vectorize(self, 200)

    def formula_2011_01_01(self, individu, period):
        return vectorize(self, 300)

    def formula_2016_01_01(self, individu, period):
        return vectorize(self, 400)


tax_benefit_system.add_variable(dated_attributes__active_formulas)


def test_call__dated_attributes__active_formulas():
    month = '1999-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__active_formulas', month) == IntCol.default

    month = '2000-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__active_formulas', month) == 100

    month = '2006-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__active_formulas', month) == 200

    month = '2011-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__active_formulas', month) == 300

    month = '2016-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__active_formulas', month) == 400


def test_dates__dated_attributes__active_formulas():
    dated_function_nb = 4

    variable = tax_benefit_system.column_by_name['dated_attributes__active_formulas']
    assert variable is not None
    assert has_dated_attribute(variable)
    assert variable.end == datetime.date(2020, 12, 31)

    # Even inactivated functions (functions with start date < attribute stop date) should be registered.
    assert variable.formula_class.dated_formulas_class.__len__() == dated_function_nb

    i = 0
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None
    # Raises an error before DatedVariable update.
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2000, 1, 1)

    i = 1
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None
    # Raises an error before DatedVariable update.
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2006, 1, 1)

    i = 2
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None
    # Raises an error before DatedVariable update.
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2011, 1, 1)

    i = 3
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None
    # Raises an error before DatedVariable update.
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2016, 1, 1)
