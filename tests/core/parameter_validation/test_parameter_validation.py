# -*- coding: utf-8 -*-

import os

from nose.tools import raises
from lxml.etree import XMLSyntaxError

from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_dummy_country.entities import entities
from openfisca_dummy_country.scenarios import Scenario


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

year = 2016


class TestTaxBenefitSystem(TaxBenefitSystem):
    def __init__(self, path_to_xml):
        TaxBenefitSystem.__init__(self, entities)
        self.Scenario = Scenario
        self.add_legislation_params(path_to_xml)


@raises(XMLSyntaxError)
def test_malformed():
    path_to_xml = os.path.join(BASE_DIR, 'malformed.xml')
    tbf = TestTaxBenefitSystem(path_to_xml)
    tbf.compute_legislation()


def test_unknown_node():
    path_to_xml = os.path.join(BASE_DIR, 'unknown_node.xml')
    tbf = TestTaxBenefitSystem(path_to_xml)
    try:
        tbf.compute_legislation()
    except ValueError as e:
        content = str(e)
        assert len(content) < 1000
        for keyword in {'unknown_node.xml:4', 'VALEU', 'not expected', 'VALUE'}:
            assert keyword in content
    else:
        assert False, "This test should raise a ValueError."


def test_wrong_value():
    path_to_xml = os.path.join(BASE_DIR, 'wrong_value.xml')
    tbf = TestTaxBenefitSystem(path_to_xml)
    try:
        tbf.compute_legislation()
    except ValueError as e:
        content = str(e)
        assert len(content) < 1000
        for keyword in {'wrong_value.xml:4', '0.3a', 'not a valid value', 'float'}:
            assert keyword in content
    else:
        assert False, "This test should raise a ValueError."


def test_wrong_bareme():
    path_to_xml = os.path.join(BASE_DIR, 'wrong_bareme.xml')
    tbf = TestTaxBenefitSystem(path_to_xml)
    try:
        tbf.compute_legislation()
    except ValueError as e:
        content = str(e)
        assert len(content) < 1000
        for keyword in {'wrong_bareme.xml:15', 'TRANCHE', 'Missing child', 'SEUIL'}:
            assert keyword in content
    else:
        assert False, "This test should raise a ValueError."
