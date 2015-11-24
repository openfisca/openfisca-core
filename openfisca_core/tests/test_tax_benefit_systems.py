# -*- coding: utf-8 -*-

import os

from nose.tools import assert_equal

from openfisca_core import legislations
from openfisca_core.taxbenefitsystems import MultipleXmlBasedTaxBenefitSystem
from openfisca_core.tests.dummy_country import entity_class_by_key_plural


source_file_dir_name = os.path.dirname(os.path.abspath(__file__))


class DummyMultipleXmlBasedTaxBenefitSystem(MultipleXmlBasedTaxBenefitSystem):
    legislation_xml_file_paths = [
        (
            os.path.join(source_file_dir_name, 'assets', 'param_root.xml'),
            None,
            ),
        (
            os.path.join(source_file_dir_name, 'assets', 'param_more.xml'),
            ('csg', 'activite'),
            ),
        ]

# Define class attributes after class declaration to avoid "name is not defined" exceptions.
DummyMultipleXmlBasedTaxBenefitSystem.entity_class_by_key_plural = entity_class_by_key_plural


def test_multiple_xml_based_tax_benefit_system():
    tax_benefit_system = DummyMultipleXmlBasedTaxBenefitSystem()
    legislation_json = tax_benefit_system.legislation_json
    assert legislation_json is not None
    assert isinstance(legislation_json, dict), legislation_json
    dated_legislation_json = legislations.generate_dated_legislation_json(legislation_json, '2012-01-01')
    assert isinstance(dated_legislation_json, dict), legislation_json
    compact_legislation = legislations.compact_dated_node_json(dated_legislation_json)
    assert_equal(compact_legislation.csg.activite.deductible.taux, 0.051)
    assert_equal(compact_legislation.csg.activite.crds.activite.taux, 0.005)
