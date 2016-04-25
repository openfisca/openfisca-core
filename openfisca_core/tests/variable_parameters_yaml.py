# -*- coding: utf-8 -*-

import os
import numpy as np

from nose.tools import assert_equal

from openfisca_core import legislations, parameters
from openfisca_core.taxbenefitsystems import MultipleXmlBasedTaxBenefitSystem
from openfisca_core.tests.dummy_country import entity_class_by_key_plural

source_file_dir_name = os.path.dirname(os.path.abspath(__file__))


class DummyMultipleXmlBasedTaxBenefitSystem(MultipleXmlBasedTaxBenefitSystem):
    legislation_xml_info_list = [
        (
            os.path.join(source_file_dir_name, 'assets', 'param_root.xml'),
            None,
        ),
        (
            os.path.join(source_file_dir_name, 'assets', 'param_more.xml'),
            ('csg', 'activite'),
        ),
    ]

    parameters_yaml_info_list = [
       os.path.join(source_file_dir_name, 'assets', 'variable_parameters.yaml'),
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

    yo = parameters.get_parameter(
            tax_benefit_system.parameters,
            'variable_parameters',
            'participation_effort_construction_2',
            '2013-09-04',
            effectif_entreprise=np.array([2, 19, 29200]),
            type_sal=np.array([1, 2, 3])
        )

    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(yo)