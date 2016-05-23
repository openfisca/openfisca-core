# -*- coding: utf-8 -*-
import os

import numpy as np
from nose.tools import assert_equal
from openfisca_core.taxbenefitsystems import MultipleXmlBasedTaxBenefitSystem

from openfisca_core import parameters
from openfisca_core.columns import IntCol, FloatCol
from openfisca_core.formulas import Variable
from openfisca_core.formula_helpers import switch
from openfisca_core.tests import dummy_country
from openfisca_core.tests.dummy_country import Individus


class choice(Variable):
    column = IntCol
    entity_class = Individus


class plafond_securite_sociale(Variable):
    column = FloatCol
    entity_class = Individus
    label = u"Plafond de la securite sociale"

    def function(self, simulation, period):
        period = period.start.period(u'month').offset('first-of')
        value = parameters.get(tax_benefit_system.parameters, 'parameters', 'plafond_securite_sociale', period.start)
        # value = self.get_parameter(period.start)
        return period, value


test_dir_path = os.path.dirname(os.path.abspath(__file__))

class DummyMultipleXmlBasedTaxBenefitSystem(MultipleXmlBasedTaxBenefitSystem):

    yaml_parameters_info_list = [
        os.path.join(test_dir_path, 'assets', 'variable_parameters.yaml'),
        os.path.join(test_dir_path, 'assets', 'parameters.yaml'),
    ]

# TaxBenefitSystem instance declared after formulas
DummyMultipleXmlBasedTaxBenefitSystem.entity_class_by_key_plural = dummy_country.entity_class_by_key_plural
DummyMultipleXmlBasedTaxBenefitSystem.Scenario = dummy_country.Scenario

tax_benefit_system = DummyMultipleXmlBasedTaxBenefitSystem()

scenario = tax_benefit_system.new_scenario().init_from_attributes(
    period = 2016,
    input_variables = {
        # 'choice': [1, 1, 1, 2],
        'choice': np.random.randint(2, size = 1000) + 1,
        },
    )


def test():
    simulation = scenario.new_simulation(debug = True)
    pss = simulation.calculate('plafond_securite_sociale')
    assert_equal(pss, 3128)


def test_get_yaml_parameter():
    assert_equal(
        parameters.get(
            tax_benefit_system.parameters,
            'parameters',
            'smic_horaire_brut',
            '2014-02-06',
        ),
        9.53
    )
