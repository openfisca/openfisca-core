# -*- coding: utf-8 -*-

from nose.tools import assert_equal

from openfisca_core import legislations
from openfisca_dummy_country import DummyTaxBenefitSystem


def test_multiple_xml_based_tax_benefit_system():
    tax_benefit_system = DummyTaxBenefitSystem()
    legislation_json = tax_benefit_system.get_legislation()
    assert legislation_json is not None
    assert isinstance(legislation_json, dict), legislation_json
    dated_legislation_json = legislations.generate_dated_legislation_json(legislation_json, '2012-01-01')
    assert isinstance(dated_legislation_json, dict), legislation_json
    compact_legislation = legislations.compact_dated_node_json(dated_legislation_json)
    assert_equal(compact_legislation.csg.activite.deductible.taux, 0.051)
    assert_equal(compact_legislation.csg.activite.crds.activite.taux, 0.005)
