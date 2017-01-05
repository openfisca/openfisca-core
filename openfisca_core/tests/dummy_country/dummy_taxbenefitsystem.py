# -*- coding: utf-8 -*-

import pkg_resources
import os

from openfisca_core.taxbenefitsystems import TaxBenefitSystem

from .entities import entities
from .scenarios import Scenario

openfisca_core_dir = pkg_resources.get_distribution('OpenFisca-Core').location
country_dir = os.path.join(openfisca_core_dir, 'openfisca_core', 'tests', 'dummy_country')
path_to_model_dir = os.path.join(country_dir, 'model')
path_to_root_params = os.path.join(country_dir, 'parameters', 'param_root.xml')
path_to_crds_params = os.path.join(country_dir, 'parameters', 'param_more.xml')


class DummyTaxBenefitSystem(TaxBenefitSystem):
    def __init__(self):
        TaxBenefitSystem.__init__(self, entities)
        self.Scenario = Scenario
        self.add_legislation_params(path_to_root_params)
        self.add_legislation_params(path_to_crds_params, 'csg.activite')
        self.add_variables_from_directory(path_to_model_dir)
