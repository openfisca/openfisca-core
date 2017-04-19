# -*- coding: utf-8 -*-

from nose.tools import assert_equal, raises

from openfisca_core import legislations
from openfisca_core.legislations import ParameterNotFound
from test_countries import tax_benefit_system


def get_legislation(instant):
    return tax_benefit_system.get_compact_legislation(instant)


def test_multiple_xml_based_tax_benefit_system():
    legislation_json = tax_benefit_system.get_legislation()
    assert legislation_json is not None
    assert isinstance(legislation_json, dict), legislation_json
    dated_legislation_json = legislations.generate_dated_legislation_json(legislation_json, '2012-01-01')
    assert isinstance(dated_legislation_json, dict), legislation_json
    compact_legislation = legislations.compact_dated_node_json(dated_legislation_json)
    assert_equal(compact_legislation.impot.taux, 0.3)
    assert_equal(compact_legislation.contribution_sociale.crds.activite.taux, 0.005)


def test_param_values():
    dated_values = {
        '1998-01-01': 0.3,
        '2014-12-31': 0.3,
        '2015-01-01': 0.32,
        '2015-12-31': 0.32,
        '2016-01-01': 0.35,
        '2050-01-01': 0.35,
        }

    for date, value in dated_values.iteritems():
        assert_equal(
            tax_benefit_system.get_compact_legislation(date).impot.taux,
            value
            )


@raises(ParameterNotFound)
def test_param_before_it_is_defined():
    tax_benefit_system.get_compact_legislation('1997-12-31').impot.taux


# The placeholder should have no effect on the parameter computation
def test_param_with_placeholder():
    assert_equal(
        tax_benefit_system.get_compact_legislation('2018-01-01').impot.isf,
        0.9
        )


def test_stopped_parameter_before_end_value():
    assert_equal(
        tax_benefit_system.get_compact_legislation('2011-12-31').impot.bouclier,
        0.6
        )


@raises(ParameterNotFound)
def test_stopped_parameter_after_end_value():
    tax_benefit_system.get_compact_legislation('2012-01-01').impot.bouclier
