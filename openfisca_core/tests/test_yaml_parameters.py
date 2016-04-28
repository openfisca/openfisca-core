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

    ###################
    # YAML parameters
    ###################

    # YAML :
    # - is less verbose than XML when the compact JSON like syntax is used for leaves, which fits very well to our VALUEs
    # - does not force escaping < in strings
    # - is less scary for non coders, feels more like natural language

    # Hierarchy is not possible though :
    # params from variable_parameters.yaml
    # are flat and all get inserted in the collection variable_parameters
    # This is a voluntary choice : hierarchy hinders programmatic and non-initiated human intervention.
    # The new VAR node type replaces hierarchy in some cases
    yaml_parameters_info_list = [
        os.path.join(source_file_dir_name, 'assets', 'variable_parameters.yaml'),
        os.path.join(source_file_dir_name, 'assets', 'parameters.yaml'),
    ]


# Define class attributes after class declaration to avoid "name is not defined" exceptions.
DummyMultipleXmlBasedTaxBenefitSystem.entity_class_by_key_plural = entity_class_by_key_plural


def test_yaml_parameters():
    tax_benefit_system = DummyMultipleXmlBasedTaxBenefitSystem()

    assert_equal(
        parameters.get(
            tax_benefit_system.parameters,
            'parameters',
            'smic_horaire_brut',
            '2014-02-06'
        )['VALUE'],
        9.53
    )

    return
    yo = parameters.get(
        tax_benefit_system.parameters,
        'variable_parameters',
        'participation_effort_construction_2',
        '2013-09-04',
        effectif_entreprise=np.array([2, 19, 29200]),
        type_sal=np.array([1, 2, 3])
    )

    print 'SALUT'
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(yo)

    assert_equal(type(yo), object)
