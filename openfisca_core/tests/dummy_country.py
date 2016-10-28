# -*- coding: utf-8 -*-


import itertools
import os
import pkg_resources
from os import path

from openfisca_core import conv
from openfisca_core.entities import build_entity
from openfisca_core.scenarios import AbstractScenario, set_entities_json_id
from openfisca_core.taxbenefitsystems import TaxBenefitSystem


openfisca_core_dir = pkg_resources.get_distribution('OpenFisca-Core').location
TEST_DIRECTORY = path.dirname(path.abspath(__file__))

# Entities


Familles = build_entity(
    key = "famille",
    plural = "familles",
    label = u'Familles',
    roles = [
        {
            'key': 'parent',
            'plural': 'parents',
            'label': u'Parents',
            'subroles': ['demandeur', 'conjoint']
            },
        {
            'key': 'enfant',
            'plural': 'enfants',
            'label': u'Enfants',
            }
        ]
    )


Individus = build_entity(
    key = "individu",
    plural = "individus",
    label = u'Individus',
    is_person = True,
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
                            conv.make_item_to_singleton(),
                            conv.test_isinstance(list),
                            conv.uniform_sequence(
                                conv.test_isinstance(dict),
                                drop_none_items = True,
                                ),
                            conv.function(set_entities_json_id),
                            conv.uniform_sequence(
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
                                            id = conv.pipe(
                                                conv.test_isinstance((basestring, int)),
                                                conv.not_none,
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
                                            if column.entity == Familles
                                            ),
                                        )),
                                    drop_none_values = True,
                                    ),
                                drop_none_items = True,
                                ),
                            conv.default({}),
                            ),
                        individus = conv.pipe(
                            conv.make_item_to_singleton(),
                            conv.test_isinstance(list),
                            conv.uniform_sequence(
                                conv.test_isinstance(dict),
                                drop_none_items = True,
                                ),
                            conv.function(set_entities_json_id),
                            conv.uniform_sequence(
                                conv.struct(
                                    dict(itertools.chain(
                                        dict(
                                            id = conv.pipe(
                                                conv.test_isinstance((basestring, int)),
                                                conv.not_none,
                                                ),
                                            ).iteritems(),
                                        (
                                            (column.name, column.json_to_python)
                                            for column in column_by_name.itervalues()
                                            if column.entity == Individus
                                            ),
                                        )),
                                    drop_none_values = True,
                                    ),
                                drop_none_items = True,
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
            familles_individus_id = [individu['id'] for individu in test_case['individus']]
            test_case, error = conv.struct(
                dict(
                    familles = conv.uniform_sequence(
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
                individu_index_by_id = {
                    individu[u'id']: individu_index
                    for individu_index, individu in enumerate(test_case[u'individus'])
                    }
                if error is None:
                    error = {}
                for individu_id in remaining_individus_id:
                    error.setdefault('individus', {})[individu_index_by_id[individu_id]] = state._(
                        u"Individual is missing from {}").format(
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

entities = [Individus, Familles]
path_to_root_params = os.path.join(openfisca_core_dir, 'openfisca_core', 'tests', 'assets', 'param_root.xml')
path_to_crds_params = os.path.join(openfisca_core_dir, 'openfisca_core', 'tests', 'assets', 'param_more.xml')


class DummyTaxBenefitSystem(TaxBenefitSystem):
    def __init__(self):
        TaxBenefitSystem.__init__(self, entities)
        self.Scenario = Scenario
        self.add_legislation_params(path_to_root_params)
        self.add_legislation_params(path_to_crds_params, 'csg.activite')
