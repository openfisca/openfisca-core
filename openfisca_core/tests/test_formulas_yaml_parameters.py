# -*- coding: utf-8 -*-
import os

import numpy as np
from nose.tools import assert_equal
from numpy.testing import assert_almost_equal

from openfisca_core import parameters
from openfisca_core.columns import FloatCol
from openfisca_core.formulas import Variable, set_input_divide_by_period, set_input_dispatch_by_period
from openfisca_core.taxbenefitsystems import MultipleXmlBasedTaxBenefitSystem
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


class effectif_entreprise(Variable):
    column = FloatCol
    entity_class = Individus
    label = "Effectif entreprise"
    set_input = set_input_dispatch_by_period


class pourcentage_alternants(Variable):
    column = FloatCol
    entity_class = Individus
    label = "Proportion de l'effectif de l'entreprise en alternance"
    set_input = set_input_dispatch_by_period


class contribution_supplementaire_apprentissage(Variable):
    column = FloatCol
    entity_class = Individus

    def function(self, simulation, period):
        instant = period.start.period(u'month').offset('first-of').start
        assiette = simulation.calculate('salaire_brut', period)

        value = self.get_parameter(instant, base_options={'base': assiette},
                                   effectif_entreprise=simulation.calculate('effectif_entreprise', period),
                                   pourcentage_alternants=simulation.calculate('pourcentage_alternants', period))
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
    period=2016,
    input_variables={
        'salaire_brut': np.array([1467, 2300, 8000]),
        'effectif_entreprise': np.array([3, 3000, 65]),
        'pourcentage_alternants': np.array([100 / 3, 0.5, 0])
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
    simulation = scenario.new_simulation(debug=True)

    pss = simulation.calculate('plafond_securite_sociale')
    assert_equal(pss[0], 3218)

    vieillesse_salarie = simulation.calculate('vieillesse_salarie')
    assert_almost_equal(vieillesse_salarie, np.array([106.36, 166.75, 250.04]), decimal=2)


def test_variable_parameters_in_formulas():
    simulation = scenario.new_simulation(debug=True)

    contrib = simulation.calculate('contribution_supplementaire_apprentissage')
    assert_almost_equal(contrib, np.array([0, .006 * 2300, .005 * 8000]), decimal=2)
