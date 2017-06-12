# -*- coding: utf-8 -*-

import datetime

from openfisca_core.model_api import Variable
from openfisca_core.periods import MONTH, ETERNITY
from openfisca_core.columns import IntCol
from openfisca_core.formulas import Formula
from openfisca_core.holders import Holder

import openfisca_country_template as country_template
from openfisca_country_template.entities import Person

# Check which date is applied whether it comes from Variable attribute (end)
# or formula(s) dates.


tax_benefit_system = country_template.CountryTaxBenefitSystem()


# HELPERS


def new_simulation(tax_benefit_system, month):
    return tax_benefit_system.new_scenario().init_from_attributes(
        period = month,
        input_variables = dict(
            ),
        ).new_simulation()


def vectorize(function, number):
    return (function.zeros() + 1) * number


def check_error_at_add_variable(tax_benefit_system, variable, error_message_prefix):
    try:
        tax_benefit_system.add_variable(variable)
    except AssertionError, e:
        if not e.message or not e.message.startswith(error_message_prefix):
            raise AssertionError('Incorrect error message. Was expecting something starting by "{}". Got: "{}"'.format(error_message_prefix, e.message).encode('utf-8'))


# TESTS


# NO END ATTRIBUTE - NO DATED FORMULA


class variable__no_date(Variable):
    column = IntCol
    entity = Person
    definition_period = MONTH
    label = u"Variable without date."


def test_before_add__variable__no_date():
    try:
        tax_benefit_system.column_by_name['variable__no_date']
    except KeyError, e:
        assert e.message == 'variable__no_date'
    except:
        raise


def test_variable__no_date():
    tax_benefit_system.add_variable(variable__no_date)
    variable = tax_benefit_system.column_by_name['variable__no_date']
    assert variable.end is None
    assert len(variable.formula_class.dated_formulas_class) == 0


# END ATTRIBUTE - NO DATED FORMULA


class variable__deprecated_start_date(Variable):
    column = IntCol
    entity = Person
    definition_period = MONTH
    label = u"Variable with end attribute and deprecated start_date attribute, no formula."
    start_date = datetime.date(1980, 1, 1)  # Deprecated
    end = '1989-12-31'


def test_add__variable__deprecated_start_date():
    check_error_at_add_variable(tax_benefit_system, variable__deprecated_start_date, 'Deprecated "start_date" attribute in definition of variable')


# end, no formula

class variable__strange_end_attribute(Variable):
    column = IntCol
    entity = Person
    definition_period = MONTH
    label = u"Variable with dubious end attribute, no formula."
    end = '1989-00-00'


def test_variable__strange_end_attribute():
    try:
        tax_benefit_system.add_variable(variable__strange_end_attribute)

    except ValueError, e:
        if e.message:
            assert e.message.startswith("Incorrect 'end' attribute format in 'variable__strange_end_attribute'."), e.message
    except:
        raise

    # Check that Error at variable adding prevents it from registration in the taxbenefitsystem.
    assert not tax_benefit_system.column_by_name.get('variable__strange_end_attribute')


# end, no formula

class variable__end_attribute(Variable):
    column = IntCol
    entity = Person
    definition_period = MONTH
    label = u"Variable with end attribute, no formula."
    end = '1989-12-31'


tax_benefit_system.add_variable(variable__end_attribute)


def test_variable__end_attribute():
    variable = tax_benefit_system.column_by_name['variable__end_attribute']
    assert variable.end == datetime.date(1989, 12, 31)


# end, one formula without date

class end_attribute__one_simple_formula(Variable):
    column = IntCol
    entity = Person
    definition_period = MONTH
    label = u"Variable with end attribute, one formula without date."
    end = '1989-12-31'

    def formula(self, individu, period):
        return vectorize(self, 100)


tax_benefit_system.add_variable(end_attribute__one_simple_formula)


def test_call__end_attribute__one_simple_formula():
    month = '1979-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('end_attribute__one_simple_formula', month) == 100

    month = '1989-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('end_attribute__one_simple_formula', month) == 100

    month = '1990-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('end_attribute__one_simple_formula', month) == IntCol.default


def test_dates__end_attribute__one_simple_formula():
    variable = tax_benefit_system.column_by_name['end_attribute__one_simple_formula']
    assert variable.end == datetime.date(1989, 12, 31)

    assert len(variable.formula_class.dated_formulas_class) == 1
    formula = variable.formula_class.dated_formulas_class[0]
    assert formula['start_instant'].date == datetime.date.min


# NO END ATTRIBUTE - DATED FORMULA(S)


# formula, strange name

class no_end_attribute__one_formula__strange_name(Variable):
    column = IntCol
    entity = Person
    definition_period = MONTH
    label = u"Variable without end attribute, one stangely named formula."

    def formula_2015_toto(self, individu, period):
        return vectorize(self, 100)


def test_add__no_end_attribute__one_formula__strange_name():
    check_error_at_add_variable(tax_benefit_system, no_end_attribute__one_formula__strange_name,
    'Unrecognized formula name. Expecting "formula_YYYY" or "formula_YYYY_MM" or "formula_YYYY_MM_DD where YYYY, MM and DD are year, month and day. Found: ')


# formula, start

class no_end_attribute__one_formula__start(Variable):
    column = IntCol
    entity = Person
    definition_period = MONTH
    label = u"Variable without end attribute, one dated formula."

    def formula_2000_01_01(self, individu, period):
        return vectorize(self, 100)


tax_benefit_system.add_variable(no_end_attribute__one_formula__start)


def test_call__no_end_attribute__one_formula__start():
    month = '1999-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_end_attribute__one_formula__start', month) == IntCol.default

    month = '2000-05'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_end_attribute__one_formula__start', month) == 100

    month = '2020-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_end_attribute__one_formula__start', month) == 100


def test_dates__no_end_attribute__one_formula__start():
    variable = tax_benefit_system.column_by_name['no_end_attribute__one_formula__start']
    assert variable.end is None

    assert len(variable.formula_class.dated_formulas_class) == 1
    formula = variable.formula_class.dated_formulas_class[0]
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2000, 1, 1)


class no_end_attribute__one_formula__eternity(Variable):
    column = IntCol
    entity = Person
    definition_period = ETERNITY  # For this entity, this variable shouldn't evolve through time
    label = u"Variable without end attribute, one dated formula."

    def formula_2000_01_01(self, individu, period):
        return vectorize(self, 100)


tax_benefit_system.add_variable(no_end_attribute__one_formula__eternity)


def test_call__no_end_attribute__one_formula__eternity():
    month = '1999-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_end_attribute__one_formula__eternity', month) == IntCol.default

    month = '2000-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_end_attribute__one_formula__eternity', month) == 100


# formula, different start formats

class no_end_attribute__formulas__start_formats(Variable):
    column = IntCol
    entity = Person
    definition_period = MONTH
    label = u"Variable without end attribute, multiple dated formulas."

    def formula_2000(self, individu, period):
        return vectorize(self, 100)

    def formula_2010_01(self, individu, period):
        return vectorize(self, 200)


tax_benefit_system.add_variable(no_end_attribute__formulas__start_formats)


def test_call__no_end_attribute__formulas__start_formats():
    month = '1999-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_end_attribute__formulas__start_formats', month) == IntCol.default

    month = '2000-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_end_attribute__formulas__start_formats', month) == 100

    month = '2009-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_end_attribute__formulas__start_formats', month) == 100

    month = '2010-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_end_attribute__formulas__start_formats', month) == 200


def test_dates__no_end_attribute__formulas__start_formats():
    variable = tax_benefit_system.column_by_name['no_end_attribute__formulas__start_formats']
    assert variable.end is None
    assert len(variable.formula_class.dated_formulas_class) == 2

    i = 0
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2000, 1, 1)

    i = 1
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2010, 1, 1)


# Multiple formulas, different names with date overlap

class no_attribute__formulas__different_names__dates_overlap(Variable):
    column = IntCol
    entity = Person
    definition_period = MONTH
    label = u"Variable, no end attribute, multiple dated formulas with different names but same dates."

    def formula_2000(self, individu, period):
        return vectorize(self, 100)

    def formula_2000_01_01(self, individu, period):
        return vectorize(self, 200)


def test_add__no_attribute__formulas__different_names__dates_overlap():
    # Variable isn't registered in the taxbenefitsystem
    check_error_at_add_variable(tax_benefit_system, no_attribute__formulas__different_names__dates_overlap, "Dated formulas overlap")


# formula(start), different names, no date overlap

class no_attribute__formulas__different_names__no_overlap(Variable):
    column = IntCol
    entity = Person
    definition_period = MONTH
    label = u"Variable, no end attribute, multiple dated formulas with different names and no date overlap."

    def formula_2000_01_01(self, individu, period):
        return vectorize(self, 100)

    def formula_2010_01_01(self, individu, period):
        return vectorize(self, 200)


tax_benefit_system.add_variable(no_attribute__formulas__different_names__no_overlap)


def test_call__no_attribute__formulas__different_names__no_overlap():
    month = '2009-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attribute__formulas__different_names__no_overlap', month) == 100

    month = '2015-05'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('no_attribute__formulas__different_names__no_overlap', month) == 200


def test_dates__no_attribute__formulas__different_names__no_overlap():
    variable = tax_benefit_system.column_by_name['no_attribute__formulas__different_names__no_overlap']
    assert len(variable.formula_class.dated_formulas_class) == 2

    i = 0
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2000, 1, 1)

    i = 1
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula['start_instant'] is not None
    assert formula['start_instant'].date == datetime.date(2010, 1, 1)


# END ATTRIBUTE - DATED FORMULA(S)


# formula, start.

class end_attribute__one_formula__start(Variable):
    column = IntCol
    entity = Person
    definition_period = MONTH
    label = u"Variable with end attribute, one dated formula."
    end = '2001-12-31'

    def formula_2000_01_01(self, individu, period):
        return vectorize(self, 100)


tax_benefit_system.add_variable(end_attribute__one_formula__start)


def test_call__end_attribute__one_formula__start():
    month = '1980-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('end_attribute__one_formula__start', month) == IntCol.default

    month = '2000-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('end_attribute__one_formula__start', month) == 100

    month = '2002-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('end_attribute__one_formula__start', month) == IntCol.default


# end < formula, start.

class stop_attribute_before__one_formula__start(Variable):
    column = IntCol
    entity = Person
    definition_period = MONTH
    label = u"Variable with stop attribute only coming before formula start."
    end = '1990-01-01'

    def formula_2000_01_01(self, individu, period):
        return vectorize(self)


def test_add__stop_attribute_before__one_formula__start():
    check_error_at_add_variable(tax_benefit_system, stop_attribute_before__one_formula__start, 'You declared that "stop_attribute_before__one_formula__start" ends on "1990-01-01", but you wrote a formula to calculate it from "2000-01-01"')


# end, formula with dates intervals overlap.

class end_attribute_restrictive__one_formula(Variable):
    column = IntCol
    entity = Person
    definition_period = MONTH
    label = u"Variable with end attribute, one dated formula and dates intervals overlap."
    end = '2001-01-01'

    def formula_2001_01_01(self, individu, period):
        return vectorize(self, 100)


tax_benefit_system.add_variable(end_attribute_restrictive__one_formula)


def test_call__end_attribute_restrictive__one_formula():
    month = '2000-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('end_attribute_restrictive__one_formula', month) == IntCol.default

    month = '2001-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('end_attribute_restrictive__one_formula', month) == 100

    month = '2000-05'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('end_attribute_restrictive__one_formula', month) == IntCol.default


# formulas of different names (without dates overlap on formulas)

class end_attribute__formulas__different_names(Variable):
    column = IntCol
    entity = Person
    definition_period = MONTH
    label = u"Variable with end attribute, multiple dated formulas with different names."
    end = '2010-12-31'

    def formula_2000_01_01(self, individu, period):
        return vectorize(self, 100)

    def formula_2005_01_01(self, individu, period):
        return vectorize(self, 200)

    def formula_2010_01_01(self, individu, period):
        return vectorize(self, 300)


tax_benefit_system.add_variable(end_attribute__formulas__different_names)


def test_call__end_attribute__formulas__different_names():
    month = '2000-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('end_attribute__formulas__different_names', month) == 100

    month = '2005-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('end_attribute__formulas__different_names', month) == 200

    month = '2010-12'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('end_attribute__formulas__different_names', month) == 300


def test_clone__end_attribute__formulas__different_names():
    # Get the formula instance to clone (in holder):
    month = '2005-01'
    simulation = new_simulation(tax_benefit_system, month)
    simulation.calculate('end_attribute__formulas__different_names', month)
    simulation_holder = simulation.get_holder('end_attribute__formulas__different_names', month)

    # clone
    variable_as_column = tax_benefit_system.column_by_name['end_attribute__formulas__different_names']  # IntCol
    new_holder = Holder(simulation, variable_as_column)
    clone = simulation_holder.formula.clone(new_holder, keys_to_skip = None)

    # Check cloned formula:
    assert isinstance(clone, Formula)
    assert clone.holder == new_holder
    assert clone.dated_formulas_class == simulation_holder.formula.dated_formulas_class
    assert clone.dated_formulas is not None
    assert len(clone.dated_formulas) == 3
    for dated_formula in clone.dated_formulas:
        assert dated_formula['formula'].holder == new_holder

    assert clone.base_function.__name__ == simulation_holder.formula.base_function.__name__  # bound methods to instances of variables
    assert clone.comments == simulation_holder.formula.comments
    assert clone.start_line_number == simulation_holder.formula.start_line_number
    assert clone.source_code == simulation_holder.formula.source_code
    assert clone.source_file_path == simulation_holder.formula.source_file_path
