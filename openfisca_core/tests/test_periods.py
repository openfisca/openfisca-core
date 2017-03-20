# -*- coding: utf-8 -*-

from nose.tools import assert_equal

from openfisca_core.periods import Period, Instant, YEAR, MONTH

first_jan = Instant((2014, 1, 1))
first_march = Instant((2014, 3, 1))

def test_year():
    assert_equal(Period((YEAR, first_jan, 1)).__str__(), u'2014')

def test_12_months_is_a_year():
    assert_equal(Period((MONTH, first_jan, 12)).__str__(), u'2014')

def test_rolling_year():
    assert_equal(Period((MONTH, first_march, 12)).__str__(), u'year:2014-03')

def test_month():
    assert_equal(Period((MONTH, first_jan, 1)).__str__(), u'2014-01')

def test_several_months():
    assert_equal(Period((MONTH, first_jan, 3)).__str__(), u'month:2014-01:3')
    assert_equal(Period((MONTH, first_march, 3)).__str__(), u'month:2014-03:3')

def test_several_years():
    assert_equal(Period((YEAR, first_jan, 3)).__str__(), u'year:2014:3')
    assert_equal(Period((YEAR, first_march, 3)).__str__(), u'year:2014-03:3')
