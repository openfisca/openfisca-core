# -*- coding: utf-8 -*-

import os

from nose.tools import assert_in, raises

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
        ('wrong_value', {'Invalid value', 'wrong_value[2015-12-01]', '1A'})
        ]

    for test in tests:
        yield (check,) + test


def test_references():
    path_to_xml = os.path.join(BASE_DIR, 'references.xml')
    tbs = TestTaxBenefitSystem(path_to_xml)
    tbs.compute_legislation()


def test_filesystem_hierarchy():
    path = os.path.join(BASE_DIR, 'filesystem_hierarchy')
    parameters = ParameterNode('', directory_path = path)
    parameters_at_instant = parameters._get_at_instant('2016-01-01')
    assert parameters_at_instant.node1.param == 1.0


def test_yaml_hierarchy():
    path = os.path.join(BASE_DIR, 'yaml_hierarchy')
    parameters = ParameterNode('', directory_path = path)
    parameters_at_instant = parameters._get_at_instant('2016-01-01')
    assert parameters_at_instant.node1.param == 1.0
