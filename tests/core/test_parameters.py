# -*- coding: utf-8 -*-

from nose.tools import assert_equal, raises
import numpy as np

from openfisca_core import legislations
from openfisca_core.legislations import ParameterNotFound
from test_countries import tax_benefit_system


def get_legislation(instant):
    return tax_benefit_system.get_compact_legislation(instant)


def test_multiple_xml_based_tax_benefit_system():
    legislation_json = tax_benefit_system.get_legislation()
    assert legislation_json is not None
    assert isinstance(legislation_json, dict), legislation_json
    dated_legislation_json = legislations.generate_dated_legislation_json(legislation_json, '2016-01-01')
    assert isinstance(dated_legislation_json, dict), legislation_json
    compact_legislation = legislations.compact_dated_node_json(dated_legislation_json)
    assert_equal(compact_legislation.taxes.income_tax_rate, 0.15)
    assert_equal(compact_legislation.benefits.basic_income, 600)


def test_param_values():
    dated_values = {
        '2015-01-01': 0.15,
        '2014-01-01': 0.14,
        '2013-01-01': 0.13,
        '2012-01-01': 0.16,
        }

    for date, value in dated_values.iteritems():
        assert_equal(
            tax_benefit_system.get_compact_legislation(date).taxes.income_tax_rate,
            value
            )


@raises(ParameterNotFound)
def test_param_before_it_is_defined():
    tax_benefit_system.get_compact_legislation('1997-12-31').taxes.income_tax_rate


# The placeholder should have no effect on the parameter computation
def test_param_with_placeholder():
    assert_equal(
        tax_benefit_system.get_compact_legislation('2018-01-01').taxes.income_tax_rate,
        0.15
        )


def test_stopped_parameter_before_end_value():
    assert_equal(
        tax_benefit_system.get_compact_legislation('2011-12-31').benefits.housing_allowance,
        0.25
        )


@raises(ParameterNotFound)
def test_stopped_parameter_after_end_value():
    tax_benefit_system.get_compact_legislation('2016-12-01').benefits.housing_allowance
