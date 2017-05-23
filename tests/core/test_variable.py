# -*- coding: utf-8 -*-

import datetime

from nose.tools import eq_
from functools import wraps

from openfisca_core.model_api import Variable
from openfisca_core.formulas import dated_function
from openfisca_core.periods import MONTH
from openfisca_core.columns import IntCol

import openfisca_dummy_country as dummy_country
from openfisca_dummy_country.entities import Individu

# Check that the most restrictive date is applied
# whether it comes from Variable attributes (start_date & stop_date)
# or function(s) decoration (@dated_function > start_instant & stop_instant).


class MyCustomException(Exception):
    pass


def raises_custom(status=None, uri=None, msg=None):
    assert status or uri or msg, 'You need to pass either status, uri, or message'

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                function(*args, **kwargs)

            except MyCustomException, e:

                def check(value, name):
                    if value:
                        eq_(getattr(e, name), value)
                check(status, 'status')
                check(uri, 'uri')
                assert getattr(e, 'message').startswith(msg)

            except:
                raise
            else:
                message = "%{} did not raise MyCustomException".format(function.__name__)
                raise AssertionError(message)
        return wrapper
    return decorator


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


def has_dated_attributes(variable):
    return (variable.start is not None) and (variable.end is not None)


def dummy_function(individu, period, number):
    # return individu('dummy_variable', period) + number
    return number


def new_simulation(tax_benefit_system, month):
    return tax_benefit_system.new_scenario().init_single_entity(
        period = month,
        parent1 = dict(
            ),
        ).new_simulation()


tax_benefit_system = dummy_country.DummyTaxBenefitSystem()


class dummy_variable(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable without date."


tax_benefit_system.add_variable(dummy_variable)


# DATED ATTRIBUTE(S) - NO DATED FORMULA


# 371 - start_date, stop_date, no function

class dated_attributes__no_formula(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with dated attributes."
    start_date = datetime.date(1980, 1, 1)
    stop_date = datetime.date(1989, 12, 31)


tax_benefit_system.add_variable(dated_attributes__no_formula)


def test_dated_attributes__no_formula():
    variable = tax_benefit_system.column_by_name['dated_attributes__no_formula']
    assert variable is not None

    assert variable.start == datetime.date(1980, 1, 1)
    assert variable.end == datetime.date(1989, 12, 31)

    assert variable.formula_class.dated_formulas_class.__len__() == 0


# 371 - start_date, stop_date, one function without date

class dated_attributes__one_formula(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with dated attributes, one function without date."
    start_date = datetime.date(1980, 1, 1)
    stop_date = datetime.date(1989, 12, 31)

    def function(individu, period, nb):
        return dummy_function(individu, period, nb)


tax_benefit_system.add_variable(dated_attributes__one_formula)


def test_dated_variable_with_one_formula():
    month = '1983-05'
    simulation = new_simulation(tax_benefit_system, month)
    result = simulation.calculate('dated_attributes__one_formula', month, nb=100)
    assert (result == 100)

    variable = tax_benefit_system.column_by_name['dated_attributes__one_formula']
    assert variable is not None

    assert variable.start == datetime.date(1980, 1, 1)
    assert variable.end == datetime.date(1989, 12, 31)

    # Formula dates should get attributes' dates
    assert variable.formula_class.dated_formulas_class.__len__() == 1
    formula = variable.formula_class.dated_formulas_class[0]
    assert formula is not None

    assert variable.start == formula['start_instant'].date
    assert variable.end == formula['stop_instant'].date


# NO DATED ATTRIBUTE - DATED FORMULA(S)

# 371 - @dated_function, start only

class no_attributes__one_start_decorated_function(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable no dated attributes, one decorated function, start only."

    @dated_function(start = datetime.date(2000, 1, 1))
    def function(individu, period, nb):
        return dummy_function(individu, period, nb)


tax_benefit_system.add_variable(no_attributes__one_start_decorated_function)


def test_no_attributes__one_function_start_only():
    month = '1983-05'
    simulation = new_simulation(tax_benefit_system, month)
    assert (simulation.calculate('no_attributes__one_start_decorated_function', month, nb=100) == 100)

    variable = tax_benefit_system.column_by_name['no_attributes__one_start_decorated_function']
    assert variable is not None

    # Formula dates should be given to attributes' dates
    # Stop should be None
    assert variable.formula_class.dated_formulas_class.__len__() == 1
    formula = variable.formula_class.dated_formulas_class[0]
    assert formula is not None

    assert formula['start_instant'].date == datetime.date(1980, 1, 1)
    assert formula['stop_instant'].date is None

    assert variable.start == formula['start_instant'].date
    assert variable.end == formula['stop_instant'].date


# 371 - @dated_function, stop only

class no_attributes__one_stop_decorated_function(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable no dated attributes, one decorated function, stop only."

    @dated_function(stop = datetime.date(2009, 12, 31))
    def function(individu, period, nb):
        return dummy_function(individu, period, nb)


tax_benefit_system.add_variable(no_attributes__one_stop_decorated_function)


def test_no_attributes__one_function_stop_only():
    month = '2008-05'
    simulation = new_simulation(tax_benefit_system, month)
    assert (simulation.calculate('no_attributes__one_stop_decorated_function', month, nb=100) == 100)

    variable = tax_benefit_system.column_by_name['no_attributes__one_stop_decorated_function']
    assert variable is not None

    # Formula dates should be given to attributes' dates
    # Start should be None (?)
    assert variable.formula_class.dated_formulas_class.__len__() == 1
    formula = variable.formula_class.dated_formulas_class[0]
    assert formula is not None

    assert formula['start_instant'].date is None
    assert formula['stop_instant'].date == datetime.date(1989, 12, 31)

    assert variable.start == formula['start_instant'].date
    assert variable.end == formula['stop_instant'].date


# 371 - @dated_function(start, stop)


class no_attributes__one_fully_decorated_function(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable no dated attributes, one fully decorated function."

    @dated_function(start = datetime.date(2000, 1, 1), stop = datetime.date(2009, 12, 31))
    def function(individu, period, nb):
        return dummy_function(individu, period, nb)


tax_benefit_system.add_variable(no_attributes__one_fully_decorated_function)


def test_no_attributes__one_formula_fully_dated():
    month = '2000-05'
    simulation = new_simulation(tax_benefit_system, month)
    assert (simulation.calculate('no_attributes__one_fully_decorated_function', month, nb=200) == 200)

    variable = tax_benefit_system.column_by_name['no_attributes__one_fully_decorated_function']
    assert variable is not None

    assert variable.formula_class.dated_formulas_class.__len__() == 1
    formula = variable.formula_class.dated_formulas_class[0]

    assert formula is not None
    assert formula['start_instant'].date == datetime.date(2000, 1, 1)
    assert formula['stop_instant'].date == datetime.date(2009, 12, 31)

    assert not has_dated_attributes(variable)
    assert variable.start == formula['start_instant'].date
    assert variable.end == formula['stop_instant'].date


# 371 - @dated_function, start only/different names with date overlap

class no_attributes__decorated_functions_multiple_names__overlap_dates(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable no dated attributes, multiple fully decorated functions with different names."

    try:
        @dated_function(start = datetime.date(2000, 1, 1), stop = datetime.date(2009, 12, 31))
        def function_100(individu, period):
            return dummy_function(individu, period, nb=100)

        @dated_function(start = datetime.date(2000, 1, 1), stop = datetime.date(2009, 12, 31))
        def function_200(individu, period):
            return dummy_function(individu, period, nb=200)

    except AssertionError, e:
        assert getattr(e, 'msg').startswith("Dated formulas overlap")
    except:
        raise


# tax_benefit_system.add_variable(no_attributes__decorated_functions_multiple_names__overlap_dates)
add_variable_catch_assertion(tax_benefit_system, no_attributes__decorated_functions_multiple_names__overlap_dates, "Dated formulas overlap")


def test_no_attributes__dated_formulas__different_names():
    # Check that AssertionError at variable adding prevents it from registration in the taxbenefitsystem.
    assert not hasattr(tax_benefit_system.column_by_name, "no_attributes__decorated_functions_multiple_names__overlap_dates")

    # dated_function_nb = 2
    # month = '2010-05'
    # simulation = new_simulation(tax_benefit_system, month)

    # assert (simulation.calculate('no_attributes__decorated_functions_multiple_names__overlap_dates', month) == 100)

    # variable = tax_benefit_system.column_by_name['no_attributes__decorated_functions_multiple_names__overlap_dates']
    # assert variable is not None
    # assert not has_dated_attributes(variable)

    # assert variable.formula_class.dated_formulas_class.__len__() == dated_function_nb
    # i = 0
    # for formula in variable.formula_class.dated_formulas_class:
    #     assert formula is not None, (dated_function_nb + " formulas expected in " + variable.formula_class.dated_formulas_class)
    #     # assert formula['formula_class'].holder is not None, ("Undefined holder for '" + variable.name + "', function#" + str(i))
    #     assert formula['start_instant'] is not None, ("Missing 'start' date on '" + variable.name + "', function#" + str(i))
    #     if i < (dated_function_nb - 1):
    #         assert formula['stop_instant'] is not None, ("Deprecated 'end' date but 'stop_instant' deduction expected on '" + variable.name + "', function#" + str(i))
    #     i += 1

    # assert (simulation.calculate('no_attributes__decorated_functions_multiple_names__overlap_dates', '2011-05') == 200)


# 371 - @dated_function, start only/same names without date overlap

class no_attributes__decorated_functions_same_name(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable no dated attributes, multiple fully decorated functions with same names."

    @dated_function(start = datetime.date(2000, 1, 1), stop = datetime.date(2009, 12, 31))
    def function(individu, period):
        return dummy_function(individu, period, nb=100)

    @dated_function(start = datetime.date(2010, 1, 1), stop = datetime.date(2019, 12, 31))  # noqa: F811
    def function(individu, period):
        return dummy_function(individu, period, nb=200)


tax_benefit_system.add_variable(no_attributes__decorated_functions_same_name)


def test_no_attributes__dated_formulas__same_names():
    dated_function_nb = 2
    month = '2010-05'
    simulation = new_simulation(tax_benefit_system, month)
    assert (simulation.calculate('no_attributes__decorated_functions_same_name', month) == 200)

    variable = tax_benefit_system.column_by_name['no_attributes__decorated_functions_same_name']
    assert variable is not None
    assert not has_dated_attributes(variable)

    assert variable.formula_class.dated_formulas_class.__len__() == dated_function_nb
    i = 0
    for formula in variable.formula_class.dated_formulas_class:
        assert formula is not None, (dated_function_nb + " formulas expected in " + variable.formula_class.dated_formulas_class)
        # assert formula['formula_class'].holder is not None, ("Undefined holder for '" + variable.name + "', function#" + str(i))
        assert formula['start_instant'] is not None, ("Missing 'start' date on '" + variable.name + "', function#" + str(i))
        if i < (dated_function_nb - 1):
            assert formula['stop_instant'] is not None, ("Deprecated 'end' date but 'stop_instant' deduction expected on '" + variable.name + "', function#" + str(i))
        i += 1

    assert (simulation.calculate('no_attributes__decorated_functions_same_name', '2005-05') == 100)


# DATED ATTRIBUTE(S) - DATED FORMULA(S)


class dated_attributes__one_start_decorated_function(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with dated attributes, one decorated function, start only."
    start_date = datetime.date(1980, 1, 1)
    stop_date = datetime.date(2001, 12, 31)

    @dated_function(start = datetime.date(2000, 1, 1))
    def function(individu, period, nb):
        return dummy_function(individu, period, nb)


tax_benefit_system.add_variable(dated_attributes__one_start_decorated_function)  # TODO Check case


class dated_attributes__one_stop_decorated_function(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with dated attributes, one decorated function, stop only."
    start_date = datetime.date(1980, 1, 1)
    stop_date = datetime.date(2001, 12, 31)

    @dated_function(stop = datetime.date(2009, 12, 31))
    def function(individu, period, nb):
        return dummy_function(individu, period, nb)


tax_benefit_system.add_variable(dated_attributes__one_stop_decorated_function)  # TODO Check case


class dated_attributes_restrictive__one_dated_function(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with dated attributes, one fully decorated function."
    start_date = datetime.date(1980, 1, 1)
    stop_date = datetime.date(2001, 12, 31)

    @dated_function(start = datetime.date(2000, 1, 1), stop = datetime.date(2009, 12, 31))
    def function(individu, period, nb):
        return dummy_function(individu, period, nb)


tax_benefit_system.add_variable(dated_attributes_restrictive__one_dated_function)


def test_dated_attributes_restrictive__one_dated_function():
    month = '1975-05'  # Older than most restrictive start.
    simulation = new_simulation(tax_benefit_system, month)
    assert (simulation.calculate('dated_attributes__decorated_functions_multiple_names', month) is None)

    month = '1999-12'  # Between attribute start and formula start.
    simulation = new_simulation(tax_benefit_system, month)
    assert (simulation.calculate('dated_attributes__decorated_functions_multiple_names', month) is None)

    month = '2001-12'  # Inside most restrictive start and stop interval.
    simulation = new_simulation(tax_benefit_system, month)
    assert (simulation.calculate('dated_attributes__decorated_functions_multiple_names', month) == 100)

    month = '2009-12'  # Between attribute stop and formula stop.
    simulation = new_simulation(tax_benefit_system, month)
    assert (simulation.calculate('dated_attributes__decorated_functions_multiple_names', month) is None)


class dated_attributes__decorated_functions_multiple_names(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with dated attributes, multiple fully decorated functions with different names."
    start_date = datetime.date(1980, 1, 1)
    stop_date = datetime.date(2001, 12, 31)

    @dated_function(start = datetime.date(2000, 1, 1), stop = datetime.date(2009, 12, 31))
    def function_100(individu, period):
        return dummy_function(individu, period, nb=100)

    @dated_function(start = datetime.date(2010, 1, 1), stop = datetime.date(2016, 12, 31))
    def function_200(individu, period):
        return dummy_function(individu, period, nb=200)


tax_benefit_system.add_variable(dated_attributes__decorated_functions_multiple_names)


# #371 - start_date, stop_date, @dated_function/different names (without dates overlap on functions)
def test_dated_variable_with_formulas__different_names():
    dated_function_nb = 2
    month = '1999-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert (simulation.calculate('dated_attributes__decorated_functions_multiple_names', month) == 100)

    variable = tax_benefit_system.column_by_name['dated_attributes__decorated_functions_multiple_names']
    assert variable is not None
    assert has_dated_attributes(variable)

    assert variable.formula_class.dated_formulas_class.__len__() == dated_function_nb

    i = 0
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None, (dated_function_nb + " formulas expected in " + variable.formula_class.dated_formulas_class)
    assert formula['start_instant'] is not None, ("'start_instant' deduced from 'start' attribute expected on '" + variable.name + "', function#" + str(i))
    assert formula['start_instant'].date == variable.start

    i = dated_function_nb - 1
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None, (dated_function_nb + " formulas expected in " + variable.formula_class.dated_formulas_class)
    assert formula['stop_instant'] is not None, ("'stop_instant' deduced from 'stop' attribute expected on '" + variable.name + "', function#" + str(i))
    assert formula['stop_instant'].date == variable.end


class dated_attributes__decorated_functions_same_name(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with dated attributes, multiple fully decorated functions with same names."
    start_date = datetime.date(1980, 1, 1)
    stop_date = datetime.date(2001, 12, 31)

    @dated_function(start = datetime.date(2000, 1, 1), stop = datetime.date(2009, 12, 31))
    def function(individu, period):
        return dummy_function(individu, period, nb=100)

    @dated_function(start = datetime.date(2010, 1, 1), stop = datetime.date(2019, 12, 31))  # noqa: F811
    def function(individu, period):
        return dummy_function(individu, period, nb=200)


tax_benefit_system.add_variable(dated_attributes__decorated_functions_same_name)


# 371 - start_date, stop_date, @dated_function/one name > api_same_function_name

def test_dated_variable_with_formulas__same_name():
    dated_function_nb = 2
    month = '1999-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__decorated_functions_same_name', month) is None

    variable = tax_benefit_system.column_by_name['dated_attributes__decorated_functions_same_name']
    assert variable is not None
    assert has_dated_attributes(variable)

    # Should take the first function declared only.
    assert variable.formula_class.dated_formulas_class.__len__() == 1

    i = 0
    formula = variable.formula_class.dated_formulas_class[i]
    assert formula is not None, (dated_function_nb + " formulas expected in " + variable.formula_class.dated_formulas_class)
    assert formula['start_instant'] is not None, ("'start_instant' deduced from 'start' attribute expected on '" + variable.name + "', function#" + str(i))
    assert formula['start_instant'].date == variable.start

    # Should apply stop_date attribute to the first function declared.
    assert formula['stop_instant'] is not None, ("'stop_instant' deduced from 'stop' attribute expected on '" + variable.name + "', function#" + str(i))
    assert formula['stop_instant'].date == variable.end


# 371 - start_date, stop_date, @dated_function/stop_date older than function start
class dated_attributes__formulas_restrictive_stop(Variable):
    column = IntCol
    entity = Individu
    definition_period = MONTH
    label = u"Variable with restrictive stop attribute, multiple fully decorated functions."
    start_date = datetime.date(1980, 1, 1)
    stop_date = datetime.date(1990, 12, 31)

    @dated_function(start = datetime.date(2000, 1, 1), stop = datetime.date(2009, 12, 31))
    def function_100(individu, period):
        return dummy_function(individu, period, nb=100)

    @dated_function(start = datetime.date(2010, 1, 1), stop = datetime.date(2019, 12, 31))
    def function_200(individu, period):
        return dummy_function(individu, period, nb=200)


tax_benefit_system.add_variable(dated_attributes__formulas_restrictive_stop)


def test_dated_variable_with_formulas__stop_date_older():
    dated_function_nb = 2
    month = '1999-01'
    simulation = new_simulation(tax_benefit_system, month)
    assert simulation.calculate('dated_attributes__formulas_restrictive_stop', month) is None

    variable = tax_benefit_system.column_by_name['dated_attributes__formulas_restrictive_stop']
    assert variable is not None
    assert has_dated_attributes(variable)

    # Should take the first function declared only.
    assert variable.formula_class.dated_formulas_class.__len__() == 1

    i = 0
    formula = variable.formula_class.dated_formulas_class[0]

    from nose.tools import set_trace
    set_trace()
    import ipdb
    ipdb.set_trace()

    assert formula is not None, (dated_function_nb + " formulas expected in " + variable.formula_class.dated_formulas_class)
    assert formula['start_instant'] is not None, ("'start_instant' deduced from 'start' attribute expected on '" + variable.name + "', function#" + str(i))
    assert formula['start_instant'].date == variable.start

    # Should apply stop_date attribute to the first function declared even if it inactivates it.
    assert formula['stop_instant'] is not None, ("'stop_date' older than 'start_instant' shouldn't be applied on '" + variable.name + "', function#" + str(i))
    assert formula['stop_instant'].date == variable.end
