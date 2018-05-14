# -*- coding: utf-8 -*-

from nose.tools import assert_equal, raises

from openfisca_core.periods import Period, Instant, YEAR, MONTH, period
from openfisca_core.commons import to_unicode

first_jan = Instant((2014, 1, 1))
first_march = Instant((2014, 3, 1))


# Test Period -> String

def test_year():
    assert_equal(to_unicode(Period((YEAR, first_jan, 1))), u'2014')


def test_12_months_is_a_year():
    assert_equal(to_unicode(Period((MONTH, first_jan, 12))), u'2014')


def test_rolling_year():
    assert_equal(to_unicode(Period((MONTH, first_march, 12))), u'year:2014-03')
    assert_equal(to_unicode(Period((YEAR, first_march, 1))), u'year:2014-03')


def test_month():
    assert_equal(to_unicode(Period((MONTH, first_jan, 1))), u'2014-01')


def test_several_months():
    assert_equal(to_unicode(Period((MONTH, first_jan, 3))), u'month:2014-01:3')
    assert_equal(to_unicode(Period((MONTH, first_march, 3))), u'month:2014-03:3')


def test_several_years():
    assert_equal(to_unicode(Period((YEAR, first_jan, 3))), u'year:2014:3')
    assert_equal(to_unicode(Period((YEAR, first_march, 3))), u'year:2014-03:3')

# Test String -> Period


def test_parsing_year():
    assert_equal(period(u'2014'), Period((YEAR, first_jan, 1)))


def test_parsing_month():
    assert_equal(period(u'2014-01'), Period((MONTH, first_jan, 1)))


def test_parsing_rolling_year():
    assert_equal(period(u'year:2014-03'), Period((YEAR, first_march, 1)))


def test_parsing_several_months():
    assert_equal(period(u'month:2014-03:3'), Period((MONTH, first_march, 3)))


def test_parsing_several_years():
    assert_equal(period(u'year:2014:2'), Period((YEAR, first_jan, 2)))


@raises(ValueError)
def test_wrong_syntax_several_years():
    period(u'2014:2')


@raises(ValueError)
def test_wrong_syntax_several_months():
    period(u'2014-2:2')


@raises(ValueError)
def test_daily_period():
    period(u'2014-2-3')


@raises(ValueError)
def test_daily_period_2():
    period(u'2014-2-3:2')


@raises(ValueError)
def test_ambiguous_period():
    period(u'month:2014')


@raises(TypeError)
def test_deprecated_signature():
    period(MONTH, 2014)


@raises(ValueError)
def test_wrong_argument():
    period({})


@raises(ValueError)
def test_wrong_argument_1():
    period([])


@raises(ValueError)
def test_none():
    period(None)


@raises(ValueError)
def test_empty_string():
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
