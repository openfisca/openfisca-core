# -*- coding: utf-8 -*-

import os

from nose.tools import assert_in, assert_equals, raises

from openfisca_core.parameters import load_parameter_file, ParameterNode, ParameterParsingError


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

year = 2016


@raises(ParameterParsingError)
def check(file_name, keywords):
    path = os.path.join(BASE_DIR, file_name) + '.yaml'
    try:
        load_parameter_file(path, file_name)
    except ParameterParsingError as e:
        content = str(e)
        for keyword in keywords:
            assert_in(keyword, content)
        raise


def test_parsing_errors():
    tests = [
        ('indentation', {'Invalid YAML', 'indentation.yaml', 'line 2', 'mapping values are not allowed'}),
        ('wrong_scale', {'Unexpected property', 'scale[1]', 'treshold'}),
        ('wrong_value', {'Invalid value', 'wrong_value[2015-12-01]', '1A'}),
        ('unexpected_key_in_parameter', {'Unexpected property', 'unexpected_key'}),
        ('wrong_type_in_parameter', {'must be of type object'}),
        ('wrong_type_in_value_history', {'must be of type object'}),
        ('unexpected_key_in_value_history', {'must be valid YYYY-MM-DD instants'}),
        ('unexpected_key_in_value_at_instant', {'Unexpected property', 'unexpected_key'}),
        ('unexpected_key_in_scale', {'Unexpected property', 'unexpected_key'}),
        ('wrong_type_in_scale', {'must be of type object'}),
        ('wrong_type_in_brackets', {'must be of type array'}),
        ('wrong_type_in_bracket', {'must be of type object'}),
        ('missing_value', {'missing', 'value'}),
        ]

    for test in tests:
        yield (check,) + test


def test_filesystem_hierarchy():
    path = os.path.join(BASE_DIR, 'filesystem_hierarchy')
    parameters = ParameterNode('', directory_path = path)
    parameters_at_instant = parameters('2016-01-01')
    assert_equals(parameters_at_instant.taxes.rate, 0.22)


def test_yaml_hierarchy():
    path = os.path.join(BASE_DIR, 'yaml_hierarchy')
    parameters = ParameterNode('', directory_path = path)
    parameters_at_instant = parameters('2016-01-01')
    assert_equals(parameters_at_instant.taxes.rate, 0.22)


def test_parameters_metadata():
    path = os.path.join(BASE_DIR, 'filesystem_hierarchy')
    parameters = ParameterNode('', directory_path = path)
    assert_equals(parameters.taxes.rate.reference, 'http://legifrance.fr/taxes/rate')
    assert_equals(parameters.taxes.rate.unit, '/1')
    assert_equals(parameters.taxes.rate.values_list[0].reference, 'http://legifrance.fr/taxes/rate/2015-12')
    assert_equals(parameters.taxes.rate.values_list[0].unit, '/1')
