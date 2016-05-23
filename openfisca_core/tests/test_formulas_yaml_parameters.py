# -*- coding: utf-8 -*-
import os

import numpy as np
from nose.tools import assert_equal, assert_true
from numpy.testing import assert_almost_equal

from openfisca_core.taxbenefitsystems import MultipleXmlBasedTaxBenefitSystem

from openfisca_core import parameters
from openfisca_core.columns import IntCol, FloatCol
from openfisca_core.formulas import Variable, set_input_divide_by_period
from openfisca_core.formula_helpers import switch
from openfisca_core.tests import dummy_country
from openfisca_core.tests.dummy_country import Individus


class salaire_brut(Variable):
    column = FloatCol
    entity_class = Individus
    label = "Salaire brut"
    set_input = set_input_divide_by_period


class plafond_securite_sociale(Variable):
    column = FloatCol
    entity_class = Individus
    label = u"Plafond de la securite sociale"

    def function(self, simulation, period):
        instant = period.start.period(u'month').offset('first-of').start
        # value = parameters.get(tax_benefit_system.parameters, 'parameters', 'plafond_securite_sociale', period.start)
        value = self.get_parameter(instant)
        return period, value


class vieillesse_deplafonnee_salarie(Variable):
    column = FloatCol
    entity_class = Individus

    def function(self, simulation, period):
        instant = period.start.period(u'month').offset('first-of').start
        pss = simulation.calculate('plafond_securite_sociale', period)
        assiette = simulation.calculate('salaire_brut', period)

        value = self.get_parameter(instant, base_options={'base': assiette, 'factor': pss})
        return period, value

class vieillesse_plafonnee_salarie(Variable):
    column = FloatCol
    entity_class = Individus

    def function(self, simulation, period):
        instant = period.start.period(u'month').offset('first-of').start
        pss = simulation.calculate('plafond_securite_sociale', period)
        assiette = simulation.calculate('salaire_brut', period)

        value = self.get_parameter(instant, base_options={'base': assiette, 'factor': pss})
        return period, value

class vieillesse_salarie(Variable):
    column = FloatCol
    entity_class = Individus

    def function(self, simulation, period):
        vieillesse = \
            simulation.calculate('vieillesse_plafonnee_salarie', period) + \
            simulation.calculate('vieillesse_deplafonnee_salarie', period)

        return period, vieillesse


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
        'salaire_brut': np.array([1467, 2300, 8000])
        },
    )



def test_simply_get_yaml_parameter():
    assert_equal(
        parameters.get(
            tax_benefit_system.parameters,
            'smic_horaire_brut',
            '2014-02-06',
        ),
        9.53
    )


def test_yaml_parameters_in_formulas():
    simulation = scenario.new_simulation(debug = True)
    pss = simulation.calculate('plafond_securite_sociale')
    assert_equal(pss[0], 3218)
    vieillesse_salarie = simulation.calculate('vieillesse_salarie')
    assert_almost_equal(vieillesse_salarie, np.array([106.36, 166.75, 250.04]), decimal=2)

