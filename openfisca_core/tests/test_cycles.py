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

# 1 <-> 2 with same period
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

# 3 <-> 4 with a period offset
@reference_formula
class variable3(SimpleFormulaColumn):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        return period, simulation.calculate('variable4', period.last_month)

@reference_formula
class variable4(SimpleFormulaColumn):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        return period, simulation.calculate('variable3', period)


@raises(AssertionError)
def test_pure_cycle():
    year = 2013
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = year,
        parent1 = dict(),
        ).new_simulation(debug = True)
    simulation.calculate('variable1')

@raises(CycleError)
def test_cycle_time_offset():
    year = 2013
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = year,
        parent1 = dict(),
        ).new_simulation(debug = True)
    simulation.calculate('variable3')
