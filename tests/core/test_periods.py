# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import

import pytest

from openfisca_core.periods import Period, Instant, YEAR, MONTH, DAY, period
from openfisca_core.commons import to_unicode

first_jan = Instant((2014, 1, 1))
first_march = Instant((2014, 3, 1))


'''
Test Period -> String
'''


# Years

def test_year():
    assert to_unicode(Period((YEAR, first_jan, 1))) == '2014'


def test_12_months_is_a_year():
    assert to_unicode(Period((MONTH, first_jan, 12))) == '2014'


def test_rolling_year():
    assert to_unicode(Period((MONTH, first_march, 12))) == 'year:2014-03'
    assert to_unicode(Period((YEAR, first_march, 1))) == 'year:2014-03'


def test_several_years():
    assert to_unicode(Period((YEAR, first_jan, 3))) == 'year:2014:3'
    assert to_unicode(Period((YEAR, first_march, 3))) == 'year:2014-03:3'


# Months

def test_month():
    assert to_unicode(Period((MONTH, first_jan, 1))) == '2014-01'


def test_several_months():
    assert to_unicode(Period((MONTH, first_jan, 3))) == 'month:2014-01:3'
    assert to_unicode(Period((MONTH, first_march, 3))) == 'month:2014-03:3'


# Days

@pytest.mark.xfail
def test_day():
    assert to_unicode(Period((DAY, first_jan, 1))) == '2014-01-01'


@pytest.mark.xfail
def test_several_days():
    assert to_unicode(Period((DAY, first_jan, 3))) == 'day:2014-01-01:3'
    assert to_unicode(Period((DAY, first_march, 3))) == 'day:2014-03-01:3'


'''
Test String -> Period
'''


# Years

def test_parsing_year():
    assert period('2014') == Period((YEAR, first_jan, 1))


def test_parsing_rolling_year():
    assert period('year:2014-03') == Period((YEAR, first_march, 1))


def test_parsing_several_years():
    assert period('year:2014:2') == Period((YEAR, first_jan, 2))


def test_wrong_syntax_several_years():
    with pytest.raises(ValueError):
        period('2014:2')


# Months

def test_parsing_month():
    assert period('2014-01') == Period((MONTH, first_jan, 1))


def test_parsing_several_months():
    assert period('month:2014-03:3') == Period((MONTH, first_march, 3))


def test_wrong_syntax_several_months():
    with pytest.raises(ValueError):
        period('2014-3:3')


# Days

@pytest.mark.xfail
def test_parsing_day():
    assert period('2014-01-01') == Period((DAY, first_jan, 1))


@pytest.mark.xfail
def test_parsing_several_days():
    assert period('day:2014-03-01:3') == Period((DAY, first_march, 3))


def test_wrong_syntax_several_days():
    with pytest.raises(ValueError):
        period('2014-2-3:2')


# Misc

def test_ambiguous_period():
    with pytest.raises(ValueError):
        period('month:2014')


def test_deprecated_signature():
    with pytest.raises(TypeError):
        period(MONTH, 2014)


def test_wrong_argument():
    with pytest.raises(ValueError):
        period({})


def test_wrong_argument_1():
    with pytest.raises(ValueError):
        period([])


def test_none():
    with pytest.raises(ValueError):
        period(None)


def test_empty_string():
    with pytest.raises(ValueError):
        period('')


def test_subperiods():

    def check_subperiods(period, unit, length, first, last):
        subperiods = period.get_subperiods(unit)
        assert len(subperiods) == length
        assert subperiods[0] == first
        assert subperiods[-1] == last

    tests = [
        (period(2017), MONTH, 12, period('2017-01'), period('2017-12')),
        (period('year:2014:2'), MONTH, 24, period('2014-01'), period('2015-12')),
        (period('month:2014-03:3'), MONTH, 3, period('2014-03'), period('2014-05')),
        (period('year:2014:2'), YEAR, 2, period('2014'), period('2015')),
        ]

    for test in tests:
        yield (check_subperiods,) + test
