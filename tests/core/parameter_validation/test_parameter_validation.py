# -*- coding: utf-8 -*-

import os

import yaml
import jsonschema

from nose.tools import assert_in, raises

from openfisca_core.parameters import Node, schema_index, schema_yaml


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

year = 2016


def test_schemas():
    jsonschema.Draft4Validator.check_schema(schema_index)
    jsonschema.Draft4Validator.check_schema(schema_yaml)


@raises(yaml.scanner.ScannerError)
def test_indentation():
    path = os.path.join(BASE_DIR, 'indentation')
    try:
        Node('', directory_path=path)
    except yaml.scanner.ScannerError as e:
        content = str(e)
        assert len(content) < 1000
        for keyword in {'indentation/param.yaml', 'line 2', 'mapping values are not allowed'}:
            assert_in(keyword, content)
        raise


@raises(ValueError)
def test_wrong_scale():
    path = os.path.join(BASE_DIR, 'wrong_scale')
    try:
        Node('', directory_path=path)
    except ValueError as e:
        content = str(e)
        assert len(content) < 1500
        for keyword in {'Invalid bracket attribute', 'scale[1]', 'treshold'}:
            assert_in(keyword, content)
        raise


@raises(ValueError)
def test_wrong_value():
    path = os.path.join(BASE_DIR, 'wrong_value')
    try:
        Node('', directory_path=path)
    except ValueError as e:
        content = str(e)
        assert len(content) < 1000
        for keyword in {'Invalid value', 'param[2015-12-01]', '1A'}:
            assert_in(keyword, content)
        raise


def test_references():
    path_to_xml = os.path.join(BASE_DIR, 'references.xml')
    tbs = TestTaxBenefitSystem(path_to_xml)
    tbs.compute_legislation()


def test_filesystem_hierarchy():
    path = os.path.join(BASE_DIR, 'filesystem_hierarchy')
    parameters = Node('', directory_path=path)
    parameters_at_instant = parameters._get_at_instant('2016-01-01')
    assert parameters_at_instant.node1.node2 == 1.0


def test_yaml_hierarchy():
    path = os.path.join(BASE_DIR, 'yaml_hierarchy')
    parameters = Node('', directory_path=path)
    parameters_at_instant = parameters._get_at_instant('2016-01-01')
    assert parameters_at_instant.node1.node2 == 1.0
