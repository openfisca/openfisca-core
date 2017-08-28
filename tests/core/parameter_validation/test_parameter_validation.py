# -*- coding: utf-8 -*-

import os

from nose.tools import assert_in, raises

from openfisca_core.parameters import ParameterNode, ParameterParsingError


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

year = 2016


@raises(ParameterParsingError)
def check(file_name, keywords):
    path = os.path.join(BASE_DIR, file_name)
    try:
        Node('', directory_path = path)
    except ParameterParsingError as e:
        content = str(e)
        for keyword in keywords:
            assert_in(keyword, content)
        raise


def test_parsing_errors():
    tests = [
        ('indentation', {'indentation/param.yaml', 'line 2', 'mapping values are not allowed'}),
        ('wrong_scale', {'Unexpected property', 'scale[1]', 'treshold'}),
        ('wrong_value', {'Invalid value', 'param[2015-12-01]', '1A'})
        ]

    for test in tests:
        yield (check,) + test


def test_references():
    path_to_xml = os.path.join(BASE_DIR, 'references.xml')
    tbs = TestTaxBenefitSystem(path_to_xml)
    tbs.compute_legislation()


def test_filesystem_hierarchy():
    path = os.path.join(BASE_DIR, 'filesystem_hierarchy')
    parameters = Node('', directory_path = path)
    parameters_at_instant = parameters._get_at_instant('2016-01-01')
    assert parameters_at_instant.node1.param == 1.0


def test_yaml_hierarchy():
    path = os.path.join(BASE_DIR, 'yaml_hierarchy')
    parameters = Node('', directory_path = path)
    parameters_at_instant = parameters._get_at_instant('2016-01-01')
    assert parameters_at_instant.node1.param == 1.0
