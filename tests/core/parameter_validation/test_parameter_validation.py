# -*- coding: utf-8 -*-

import os

import yaml
import jsonschema

from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_country_template.entities import entities


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

year = 2016


class TestTaxBenefitSystem(TaxBenefitSystem):
    def __init__(self, path_to_json):
        TaxBenefitSystem.__init__(self, entities)
        self.add_legislation_params(path_to_json)


def test_indentation():
    path_to_json = os.path.join(BASE_DIR, 'indentation')
    tbs = TestTaxBenefitSystem(path_to_json)
    try:
        tbs.compute_legislation()
    except yaml.scanner.ScannerError as e:
        content = str(e)
        assert len(content) < 1000
        for keyword in {'indentation/param.yaml', 'line 2', 'mapping values are not allowed here'}:
            assert keyword in content
    else:
        assert False, "This test should raise a ScannerError."


def test_wrong_scale():
    path_to_json = os.path.join(BASE_DIR, 'wrong_scale')
    tbs = TestTaxBenefitSystem(path_to_json)
    try:
        tbs.compute_legislation()
    except jsonschema.exceptions.ValidationError as e:
        content = str(e)
        assert len(content) < 1500
        for keyword in {'is not valid under any of the given schemas'}:
            assert keyword in content
    else:
        assert False, "This test should raise a ValidationError."


def test_wrong_type():
    path_to_json = os.path.join(BASE_DIR, 'wrong_type')
    tbs = TestTaxBenefitSystem(path_to_json)
    try:
        tbs.compute_legislation()
    except jsonschema.exceptions.ValidationError as e:
        content = str(e)
        assert len(content) < 1000
        for keyword in {'thistypedoesnotexist', 'node'}:
            assert keyword in content
    else:
        assert False, "This test should raise a ValidationError."


def test_wrong_value():
    path_to_json = os.path.join(BASE_DIR, 'wrong_value')
    tbs = TestTaxBenefitSystem(path_to_json)
    try:
        tbs.compute_legislation()
    except jsonschema.exceptions.ValidationError as e:
        content = str(e)
        assert len(content) < 1000
        for keyword in {'is not valid under any of the given schemas'}:
            assert keyword in content
    else:
        assert False, "This test should raise a ValidationError."


def test_references():
    path_to_xml = os.path.join(BASE_DIR, 'references.xml')
    tbs = TestTaxBenefitSystem(path_to_xml)
    tbs.compute_legislation()


def test_filesystem_hierarchy():
    path_to_json = os.path.join(BASE_DIR, 'filesystem_hierarchy')
    tbs = TestTaxBenefitSystem(path_to_json)
    tbs.compute_legislation()
    legislation = tbs.get_legislation_at_instant('2016-01-01')
    assert legislation.node1.node2 == 1.0


def test_yaml_hierarchy():
    path_to_json = os.path.join(BASE_DIR, 'yaml_hierarchy')
    tbs = TestTaxBenefitSystem(path_to_json)
    tbs.compute_legislation()
    legislation = tbs.get_legislation_at_instant('2016-01-01')
    assert legislation.node1.node2 == 1.0
