# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import collections
import datetime
import itertools

import numpy as np
from numpy.core.defchararray import startswith
from nose.tools import raises

from openfisca_core import conv, periods
from openfisca_core.columns import BoolCol, DateCol, FixedStrCol, FloatCol, IntCol
from openfisca_core.entities import AbstractEntity
from openfisca_core.formulas import (dated_function, DatedFormulaColumn, EntityToPersonColumn,
    make_formula_decorator, PersonToEntityColumn, reference_input_variable, set_input_divide_by_period,
    SimpleFormulaColumn, CycleError)
from openfisca_core.scenarios import AbstractScenario, set_entities_json_id
from openfisca_core.taxbenefitsystems import AbstractTaxBenefitSystem
from openfisca_core.tools import assert_near
from openfisca_core.tests.test_countries import *

# TaxBenefitSystem instance declared after formulas
TaxBenefitSystem = init_country()
tax_benefit_system = TaxBenefitSystem()

reference_formula = make_formula_decorator(entity_class_by_symbol = entity_class_by_symbol)


# 1 <--> 2 with same period
@reference_formula
class variable1(SimpleFormulaColumn):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        return period, simulation.calculate('variable2', period)


@reference_formula
class variable2(SimpleFormulaColumn):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        return period, simulation.calculate('variable1', period)


# 3 <--> 4 with a period offset, but without explicit cycle allowed
@reference_formula
class variable3(SimpleFormulaColumn):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        return period, simulation.calculate('variable4', period.last_year)


@reference_formula
class variable4(SimpleFormulaColumn):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        return period, simulation.calculate('variable3', period)


# 5 -f-> 6 with a period offset, with cycle flagged but not allowed
#   <---
@reference_formula
class variable5(SimpleFormulaColumn):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        variable6 = simulation.calculate('variable6', period.last_year, max_nb_recursive_calls = 0)
        return period, 5 + variable6


@reference_formula
class variable6(SimpleFormulaColumn):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        variable5 = simulation.calculate('variable5', period)
        return period, 6 + variable5


# december cotisation depending on november value
@reference_formula
class cotisation(SimpleFormulaColumn):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        period = period.this_month
        if period.start.month == 12:
            return period, 2 *   simulation.calculate('cotisation', period.last_month, max_nb_recursive_calls = 1)
        else:
            return period, self.zeros() + 1

# 7 -f-> 8 with a period offset, with explicit cycle allowed (1 level)
#   <---
@reference_formula
class variable7(SimpleFormulaColumn):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        variable8 = simulation.calculate('variable8', period.last_year, max_nb_recursive_calls = 1)
        return period, 7 + variable8

@reference_formula
class variable8(SimpleFormulaColumn):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        variable7 = simulation.calculate('variable7', period)
        return period, 8 + variable7

reference_period = periods.period(u'2013')


@raises(AssertionError)
def test_pure_cycle():
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = reference_period,
        parent1 = dict(),
        ).new_simulation(debug = True)
    simulation.calculate('variable1')


@raises(CycleError)
def test_cycle_time_offset():
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = reference_period,
        parent1 = dict(),
        ).new_simulation(debug = True)
    simulation.calculate('variable3')


# On teste en calculant variable5 et variable6 dans un ordre puis dans l'autre, pour vérifier que
# le point d'entrée dans le cycle n'a pas d'influence sur le résultat.
def test_allowed_cycle():
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = reference_period,
        parent1 = dict(),
        ).new_simulation(debug = True)
    variable6 = simulation.calculate('variable6')
    variable5 = simulation.calculate('variable5')
    variable6_last_year = simulation.calculate('variable6', reference_period.last_year)
    assert_near(variable5, [5])
    assert_near(variable6, [11])
    assert_near(variable6_last_year, [0])


def test_allowed_cycle_bis():
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = reference_period,
        parent1 = dict(),
        ).new_simulation(debug = True)
    variable5 = simulation.calculate('variable5')
    variable6 = simulation.calculate('variable6')
    variable6_last_year = simulation.calculate('variable6', reference_period.last_year)
    assert_near(variable5, [5])
    assert_near(variable6, [11])
    assert_near(variable6_last_year, [0])


def test_cotisation_1_level():
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = reference_period.last_month,  # December
        parent1 = dict(),
        ).new_simulation(debug = True)
    cotisation = simulation.calculate('cotisation')
    assert_near(cotisation, [2])


def test_cycle_1_level():
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = reference_period,
        parent1 = dict(),
        ).new_simulation(debug = True)
    variable7 = simulation.calculate('variable7')
    # variable8 = simulation.calculate('variable8')
    assert_near(variable7, [22])
