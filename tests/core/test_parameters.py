# -*- coding: utf-8 -*-

from nose.tools import assert_equal, raises
import tempfile

from openfisca_core.parameters import ParameterNotFound, ParameterNode, ParameterNodeAtInstant, load_parameter_file
from .test_countries import tax_benefit_system


def test_get_at_instant():
    parameters = tax_benefit_system.parameters
    assert isinstance(parameters, ParameterNode), parameters
    parameters_at_instant = parameters('2016-01-01')
    assert isinstance(parameters_at_instant, ParameterNodeAtInstant), parameters_at_instant
    assert parameters_at_instant.taxes.income_tax_rate == 0.15
    assert parameters_at_instant.benefits.basic_income == 600


def test_param_values():
    dated_values = {
        '2015-01-01': 0.15,
        '2014-01-01': 0.14,
        '2013-01-01': 0.13,
        '2012-01-01': 0.16,
        }

    for date, value in dated_values.items():
        assert_equal(
            tax_benefit_system.get_parameters_at_instant(date).taxes.income_tax_rate,
            value
            )


@raises(ParameterNotFound)
def test_param_before_it_is_defined():
    tax_benefit_system.get_parameters_at_instant('1997-12-31').taxes.income_tax_rate


# The placeholder should have no effect on the parameter computation
def test_param_with_placeholder():
    assert_equal(
        tax_benefit_system.get_parameters_at_instant('2018-01-01').taxes.income_tax_rate,
        0.15
        )


def test_stopped_parameter_before_end_value():
    assert_equal(
        tax_benefit_system.get_parameters_at_instant('2011-12-31').benefits.housing_allowance,
        0.25
        )


@raises(ParameterNotFound)
def test_stopped_parameter_after_end_value():
    tax_benefit_system.get_parameters_at_instant('2016-12-01').benefits.housing_allowance


def test_parameter_for_period():
    income_tax_rate = tax_benefit_system.parameters.taxes.income_tax_rate
    assert income_tax_rate("2015") == income_tax_rate("2015-01-01")


@raises(ValueError)
def test_wrong_value():
    income_tax_rate = tax_benefit_system.parameters.taxes.income_tax_rate
    income_tax_rate("test")


def test_parameter_repr():
    parameters = tax_benefit_system.parameters
    tf = tempfile.NamedTemporaryFile(delete = False)
    tf.write(repr(parameters).encode('utf-8'))
    tf.close()
    tf_parameters = load_parameter_file(file_path = tf.name)
    assert repr(parameters) == repr(tf_parameters)


def test_parameters_metadata():
    parameter = tax_benefit_system.parameters.benefits.basic_income
    assert parameter.metadata['reference'] == 'https://law.gov.example/basic-income/amount'
    assert parameter.metadata['unit'] == 'currency-EUR'
    assert parameter.values_list[0].metadata['reference'] == 'https://law.gov.example/basic-income/amount/2015-12'
    assert parameter.values_list[0].metadata['unit'] == 'currency-EUR'
    scale = tax_benefit_system.parameters.taxes.social_security_contribution
    assert scale.metadata['threshold_unit'] == 'currency-EUR'
    assert scale.metadata['rate_unit'] == '/1'


def test_parameter_node_metadata():
    parameter = tax_benefit_system.parameters.benefits
    assert parameter.description == 'Social benefits'

    parameter_2 = tax_benefit_system.parameters.taxes.housing_tax
    assert parameter_2.description == 'Housing tax'


def test_parameter_documentation():
    parameter = tax_benefit_system.parameters.benefits.housing_allowance
    assert_equal(parameter.documentation,
        'A fraction of the rent.\nFrom the 1st of Dec 2016, the housing allowance no longer exists.\n')


def test_get_descendants():
    all_parameters = {parameter.name for parameter in tax_benefit_system.parameters.get_descendants()}
    assert all_parameters.issuperset({'taxes', 'taxes.housing_tax', 'taxes.housing_tax.minimal_amount'})


def test_name():
    parameter_data = {
        "description": "Parameter indexed by a numeric key",
        "2010": {
            "values": {
                '2006-01-01': 0.0075
                }
            }
        }
    parameter = ParameterNode('root', data = parameter_data)
    assert parameter.children["2010"].name == "root.2010"
