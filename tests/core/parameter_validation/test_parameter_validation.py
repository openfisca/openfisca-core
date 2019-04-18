# -*- coding: utf-8 -*-

import os
import pytest
from openfisca_core.parameters import load_parameter_file, ParameterNode, ParameterParsingError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
year = 2016


def check(file_name, keywords):
    path = os.path.join(BASE_DIR, file_name) + '.yaml'
    try:
        load_parameter_file(path, file_name)
    except ParameterParsingError as e:
        content = str(e)
        for keyword in keywords:
            assert keyword in content
        raise


@pytest.mark.parametrize("test", [
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
    ('duplicate_key', {'duplicate'}),
    ])
def test_parsing_errors(test):
    with pytest.raises(ParameterParsingError):
        check(*test)


def test_filesystem_hierarchy():
    path = os.path.join(BASE_DIR, 'filesystem_hierarchy')
    parameters = ParameterNode('', directory_path = path)
    parameters_at_instant = parameters('2016-01-01')
    assert parameters_at_instant.node1.param == 1.0


def test_yaml_hierarchy():
    path = os.path.join(BASE_DIR, 'yaml_hierarchy')
    parameters = ParameterNode('', directory_path = path)
    parameters_at_instant = parameters('2016-01-01')
    assert parameters_at_instant.node1.param == 1.0
