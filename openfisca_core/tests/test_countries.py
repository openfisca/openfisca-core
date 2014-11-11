# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
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

from openfisca_core import conv, periods
from openfisca_core.columns import BoolCol, FixedStrCol, FloatCol, IntCol, reference_input_variable
from openfisca_core.entities import AbstractEntity
from openfisca_core.formulas import (dated_function, DatedFormulaColumn, EntityToPersonColumn, PersonToEntityColumn,
    make_reference_formula_decorator, SimpleFormulaColumn)
from openfisca_core.scenarios import AbstractScenario
from openfisca_core.taxbenefitsystems import AbstractTaxBenefitSystem
from openfisca_core.tools import assert_near


# Entities


class Familles(AbstractEntity):
    column_by_name = collections.OrderedDict()
    index_for_person_variable_name = 'id_famille'
    key_plural = 'familles'
    key_singular = 'famille'
    label = u'Famille'
    max_cardinality_by_role_key = {'parents': 2}
    name_key = 'nom_famille'
    role_for_person_variable_name = 'role_dans_famille'
    roles_key = ['parents', 'enfants']
    label_by_role_key = {
        'enfants': u'Enfants',
        'parents': u'Parents',
        }
    symbol = 'fam'

    def iter_member_persons_role_and_id(self, member):
        role = 0

        parents_id = member['parents']
        assert 1 <= len(parents_id) <= 2
        for parent_role, parent_id in enumerate(parents_id, role):
            assert parent_id is not None
            yield parent_role, parent_id
        role += 2

        enfants_id = member.get('enfants')
        if enfants_id is not None:
            for enfant_role, enfant_id in enumerate(enfants_id, role):
                assert enfant_id is not None
                yield enfant_role, enfant_id


class Individus(AbstractEntity):
    column_by_name = collections.OrderedDict()
    is_persons_entity = True
    key_plural = 'individus'
    key_singular = 'individu'
    label = u'Personne'
    name_key = 'nom_individu'
    symbol = 'ind'


entity_class_by_symbol = dict(
    fam = Familles,
    ind = Individus,
    )


# Scenarios


class Scenario(AbstractScenario):
    def init_single_entity(self, axes = None, enfants = None, famille = None, parent1 = None, parent2 = None,
            period = None):
        if enfants is None:
            enfants = []
        assert parent1 is not None
        famille = famille.copy() if famille is not None else {}
        individus = []
        for index, individu in enumerate([parent1, parent2] + (enfants or [])):
            if individu is None:
                continue
            id = individu.get('id')
            if id is None:
                individu = individu.copy()
                individu['id'] = id = 'ind{}'.format(index)
            individus.append(individu)
            if index <= 1:
                famille.setdefault('parents', []).append(id)
            else:
                famille.setdefault('enfants', []).append(id)
        conv.check(self.make_json_or_python_to_attributes())(dict(
            axes = axes,
            period = period,
            test_case = dict(
                familles = [famille],
                individus = individus,
                ),
            ))
        return self

    def make_json_or_python_to_test_case(self, period = None, repair = False):
        assert period is not None

        def json_or_python_to_test_case(value, state = None):
            if value is None:
                return value, None
            if state is None:
                state = conv.default_state

            column_by_name = self.tax_benefit_system.column_by_name

            # First validation and conversion step
            test_case, error = conv.pipe(
                conv.test_isinstance(dict),
                conv.struct(
                    dict(
                        familles = conv.pipe(
                            conv.condition(
                                conv.test_isinstance(list),
                                conv.pipe(
                                    conv.uniform_sequence(
                                        conv.test_isinstance(dict),
                                        drop_none_items = True,
                                        ),
                                    conv.function(lambda values: collections.OrderedDict(
                                        (value.pop('id', index), value)
                                        for index, value in enumerate(values)
                                        )),
                                    ),
                                ),
                            conv.test_isinstance(dict),
                            conv.uniform_mapping(
                                conv.pipe(
                                    conv.test_isinstance((basestring, int)),
                                    conv.not_none,
                                    ),
                                conv.pipe(
                                    conv.test_isinstance(dict),
                                    conv.struct(
                                        dict(itertools.chain(
                                            dict(
                                                enfants = conv.pipe(
                                                    conv.test_isinstance(list),
                                                    conv.uniform_sequence(
                                                        conv.test_isinstance((basestring, int)),
                                                        drop_none_items = True,
                                                        ),
                                                    conv.default([]),
                                                    ),
                                                parents = conv.pipe(
                                                    conv.test_isinstance(list),
                                                    conv.uniform_sequence(
                                                        conv.test_isinstance((basestring, int)),
                                                        drop_none_items = True,
                                                        ),
                                                    conv.default([]),
                                                    ),
                                                ).iteritems(),
                                            (
                                                (column.name, column.json_to_python)
                                                for column in column_by_name.itervalues()
                                                if column.entity == 'fam'
                                                ),
                                            )),
                                        drop_none_values = True,
                                        ),
                                    ),
                                drop_none_values = True,
                                ),
                            conv.default({}),
                            ),
                        individus = conv.pipe(
                            conv.condition(
                                conv.test_isinstance(list),
                                conv.pipe(
                                    conv.uniform_sequence(
                                        conv.test_isinstance(dict),
                                        drop_none_items = True,
                                        ),
                                    conv.function(lambda values: collections.OrderedDict(
                                        (value.pop('id', index), value)
                                        for index, value in enumerate(values)
                                        )),
                                    ),
                                ),
                            conv.test_isinstance(dict),
                            conv.uniform_mapping(
                                conv.pipe(
                                    conv.test_isinstance((basestring, int)),
                                    conv.not_none,
                                    ),
                                conv.pipe(
                                    conv.test_isinstance(dict),
                                    conv.struct(
                                        dict(
                                            (column.name, column.json_to_python)
                                            for column in column_by_name.itervalues()
                                            if column.entity == 'ind' and column.name not in (
                                                'idfam', 'idfoy', 'idmen', 'quifam', 'quifoy', 'quimen')
                                            ),
                                        drop_none_values = True,
                                        ),
                                    ),
                                drop_none_values = True,
                                ),
                            conv.empty_to_none,
                            conv.not_none,
                            ),
                        ),
                    ),
                )(value, state = state)
            if error is not None:
                return test_case, error

            # Second validation step
            familles_individus_id = list(test_case['individus'].iterkeys())
            test_case, error = conv.struct(
                dict(
                    familles = conv.uniform_mapping(
                        conv.noop,
                        conv.struct(
                            dict(
                                enfants = conv.uniform_sequence(conv.test_in_pop(familles_individus_id)),
                                parents = conv.uniform_sequence(conv.test_in_pop(familles_individus_id)),
                                ),
                            default = conv.noop,
                            ),
                        ),
                    ),
                default = conv.noop,
                )(test_case, state = state)

            remaining_individus_id = set(familles_individus_id)
            if remaining_individus_id:
                if error is None:
                    error = {}
                for individu_id in remaining_individus_id:
                    error.setdefault('individus', {})[individu_id] = state._(u"Individual is missing from {}").format(
                        state._(u' & ').join(
                            word
                            for word in [
                                u'familles' if individu_id in familles_individus_id else None,
                                ]
                            if word is not None
                            ))
            if error is not None:
                return test_case, error

            return test_case, error

        return json_or_python_to_test_case


# TaxBenefitSystems


def init_country():
    class TaxBenefitSystem(AbstractTaxBenefitSystem):
        entity_class_by_key_plural = {
            entity_class.key_plural: entity_class
            for entity_class in entity_class_by_symbol.itervalues()
            }

    # Define class attributes after class declaration to avoid "name is not defined" exceptions.
    TaxBenefitSystem.Scenario = Scenario

    return TaxBenefitSystem


# Input variables


reference_input_variable(
    column = FixedStrCol(max_length = 5),
    entity_class = Familles,
    is_permanent = True,
    label = u"""Code INSEE "depcom" de la commune de résidence de la famille""",
    name = 'depcom',
    )


reference_input_variable(
    column = IntCol,
    entity_class = Individus,
    is_permanent = True,
    label = u"Identifiant de la famille",
    name = 'id_famille',
    )


reference_input_variable(
    column = IntCol,
    entity_class = Individus,
    is_permanent = True,
    label = u"Rôle dans la famille",
    name = 'role_dans_famille',
    )


reference_input_variable(
    column = FloatCol,
    entity_class = Individus,
    label = "Salaire brut",
    name = 'salaire_brut',
    )


# Calculated variables


reference_formula = make_reference_formula_decorator(entity_class_by_symbol = entity_class_by_symbol)


@reference_formula
class dom_tom(SimpleFormulaColumn):
    column = BoolCol
    entity_class = Familles
    label = u"La famille habite-t-elle les DOM-TOM ?"

    def function(self, depcom):
        return np.logical_or(startswith(depcom, '97'), startswith(depcom, '98'))

    def get_output_period(self, period):
        return period.start.period(u'year').offset('first-of')


@reference_formula
class dom_tom_individu(EntityToPersonColumn):
    entity_class = Individus
    label = u"La personne habite-t-elle les DOM-TOM ?"
    variable = dom_tom


@reference_formula
class revenu_disponible(SimpleFormulaColumn):
    column = FloatCol
    entity_class = Individus
    label = u"Revenu disponible de l'individu"

    def function(self, rsa, salaire_imposable):
        return rsa + salaire_imposable * 0.7

    def get_output_period(self, period):
        return period.start.period(u'year').offset('first-of')


@reference_formula
class revenu_disponible_famille(PersonToEntityColumn):
    entity_class = Familles
    label = u"Revenu disponible de la famille"
    operation = 'add'
    variable = revenu_disponible


@reference_formula
class rsa(DatedFormulaColumn):
    column = FloatCol
    entity_class = Individus
    label = u"RSA"

    @dated_function(datetime.date(2010, 1, 1))
    def function_2010(self, salaire_imposable):
        return (salaire_imposable < 500) * 100.0

    @dated_function(datetime.date(2011, 1, 1), datetime.date(2012, 12, 31))
    def function_2011_2012(self, salaire_imposable):
        return (salaire_imposable < 500) * 200.0

    @dated_function(datetime.date(2013, 1, 1))
    def function_2013(self, salaire_imposable):
        return (salaire_imposable < 500) * 300

    def get_output_period(self, period):
        return period.start.period(u'month').offset('first-of')


@reference_formula
class salaire_imposable(SimpleFormulaColumn):
    column = FloatCol
    entity_class = Individus
    label = u"Salaire imposable"

    def function(self, dom_tom_individu, salaire_net):
        return salaire_net * 0.9 - 100 * dom_tom_individu

    def get_output_period(self, period):
        return period.start.period(u'year').offset('first-of')


@reference_formula
class salaire_net(SimpleFormulaColumn):
    column = FloatCol
    entity_class = Individus
    label = u"Salaire net"

    @staticmethod
    def function(salaire_brut):
        return salaire_brut * 0.8

    def get_output_period(self, period):
        return period.start.period(u'year').offset('first-of')


# TaxBenefitSystem instance declared after formulas


TaxBenefitSystem = init_country()
tax_benefit_system = TaxBenefitSystem()


def test_1_axis():
    year = 2013
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            dict(
                count = 3,
                name = 'salaire_brut',
                max = 100000,
                min = 0,
                ),
            ],
        period = year,
        parent1 = {},
        parent2 = {},
        ).new_simulation(debug = True)
    assert_near(simulation.calculate('revenu_disponible_famille'), [7200, 28800, 54000], error_margin = 0.005)


def test_2_parallel_axes_1_constant():
    year = 2013
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            [
                dict(
                    count = 3,
                    name = 'salaire_brut',
                    max = 100000,
                    min = 0,
                    ),
                dict(
                    count = 3,
                    index = 1,
                    name = 'salaire_brut',
                    max = 0.0001,
                    min = 0,
                    ),
                ],
            ],
        period = year,
        parent1 = {},
        parent2 = {},
        ).new_simulation(debug = True)
    assert_near(simulation.calculate('revenu_disponible_famille'), [7200, 28800, 54000], error_margin = 0.005)


def test_2_parallel_axes_same_values():
    year = 2013
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            [
                dict(
                    count = 3,
                    name = 'salaire_brut',
                    max = 100000,
                    min = 0,
                    ),
                dict(
                    count = 3,
                    index = 1,
                    name = 'salaire_brut',
                    max = 100000,
                    min = 0,
                    ),
                ],
            ],
        period = year,
        parent1 = {},
        parent2 = {},
        ).new_simulation(debug = True)
    assert_near(simulation.calculate('revenu_disponible_famille'), [7200, 50400, 100800], error_margin = 0.005)


def check_revenu_disponible(year, depcom, expected_revenu_disponible):
    global tax_benefit_system
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            dict(
                count = 3,
                name = 'salaire_brut',
                max = 100000,
                min = 0,
                ),
            ],
        famille = dict(depcom = depcom),
        period = periods.period(year),
        parent1 = dict(),
        parent2 = dict(),
        ).new_simulation(debug = True)
    revenu_disponible = simulation.calculate('revenu_disponible')
    assert_near(revenu_disponible, expected_revenu_disponible, error_margin = 0.005)
    revenu_disponible_famille = simulation.calculate('revenu_disponible_famille')
    expected_revenu_disponible_famille = np.array([
        expected_revenu_disponible[i] + expected_revenu_disponible[i + 1]
        for i in range(0, len(expected_revenu_disponible), 2)
        ])
    assert_near(revenu_disponible_famille, expected_revenu_disponible_famille, error_margin = 0.005)


def test_revenu_disponible():
    yield check_revenu_disponible, 2009, '75101', np.array([0, 0, 25200, 0, 50400, 0])
    yield check_revenu_disponible, 2010, '75101', np.array([1200, 1200, 25200, 1200, 50400, 1200])
    yield check_revenu_disponible, 2011, '75101', np.array([2400, 2400, 25200, 2400, 50400, 2400])
    yield check_revenu_disponible, 2012, '75101', np.array([2400, 2400, 25200, 2400, 50400, 2400])
    yield check_revenu_disponible, 2013, '75101', np.array([3600, 3600, 25200, 3600, 50400, 3600])

    yield check_revenu_disponible, 2009, '97123', np.array([-70.0, -70.0, 25130.0, -70.0, 50330.0, -70.0])
    yield check_revenu_disponible, 2010, '97123', np.array([1130.0, 1130.0, 25130.0, 1130.0, 50330.0, 1130.0])
    yield check_revenu_disponible, 2011, '98456', np.array([2330.0, 2330.0, 25130.0, 2330.0, 50330.0, 2330.0])
    yield check_revenu_disponible, 2012, '98456', np.array([2330.0, 2330.0, 25130.0, 2330.0, 50330.0, 2330.0])
    yield check_revenu_disponible, 2013, '98456', np.array([3530.0, 3530.0, 25130.0, 3530.0, 50330.0, 3530.0])
