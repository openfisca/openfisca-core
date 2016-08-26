# -*- coding: utf-8 -*-


import itertools
import os
import pkg_resources
from os import path

from openfisca_core import conv
from openfisca_core.columns import IntCol
from openfisca_core.variables import Variable
from openfisca_core.simulations import AbstractSimulation, set_entities_json_id
from openfisca_core.taxbenefitsystems import TaxBenefitSystem


openfisca_core_dir = pkg_resources.get_distribution('OpenFisca-Core').location
TEST_DIRECTORY = path.dirname(path.abspath(__file__))

# Entities

def iter_member_persons_role_and_id(member):
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


Familles = frozenset([
    ('index_for_person_variable_name', 'id_famille'),
    ('key_plural', 'familles'),
    ('key_singular', 'famille'),
    ('label', u'Famille'),
    ('max_cardinality_by_role_key', frozenset([
        ('parents', 2)
        ])),
    ('role_for_person_variable_name', 'role_dans_famille'),
    ('roles_key', frozenset(['parents', 'enfants'])),
    ('label_by_role_key', frozenset([
        ('enfants', u'Enfants'),
        ('parents', u'Parents'),
        ])),
    ('symbol', 'fam'),
    ('iter_member_persons_role_and_id', iter_member_persons_role_and_id),
])



Individus = frozenset([
    ('index_for_person_variable_name', None),
    ('role_for_person_variable_name', None),
    ('is_persons_entity', True),
    ('key_plural', 'individus'),
    ('key_singular', 'individu'),
    ('label', u'Personne'),
    ('symbol', 'ind'),
])


# Mandatory input variables


class id_famille(Variable):
    column = IntCol
    entity_class = Individus
    is_permanent = True
    label = u"Identifiant de la famille"


class role_dans_famille(Variable):
    column = IntCol
    entity_class = Individus
    is_permanent = True
    label = u"Rôle dans la famille"

# Simulation


class Simulation(AbstractSimulation):
    def __init__(self, tbs, axes=None, enfants=None, famille=None, parent1=None, parent2=None,
            period=None):
        self.tax_benefit_system = tbs

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
            axes=axes,
            period=period,
            test_case=dict(
                familles=[famille],
                individus=individus,
                ),
            ))

        super(Simulation, self).__init__(tbs)

    def make_json_or_python_to_test_case(self, period=None, repair=False):
        assert period is not None

        def json_or_python_to_test_case(value, state=None):
            if value is None:
                return value, None
            if state is None:
                state = conv.default_state

            variable_class_by_name = self.tax_benefit_system.variable_class_by_name

            # First validation and conversion step
            test_case, error = conv.pipe(
                conv.test_isinstance(dict),
                conv.struct(
                    dict(
                        familles=conv.pipe(
                            conv.make_item_to_singleton(),
                            conv.test_isinstance(list),
                            conv.uniform_sequence(
                                conv.test_isinstance(dict),
                                drop_none_items=True,
                                ),
                            conv.function(set_entities_json_id),
                            conv.uniform_sequence(
                                conv.struct(
                                    dict(itertools.chain(
                                        dict(
                                            enfants=conv.pipe(
                                                conv.test_isinstance(list),
                                                conv.uniform_sequence(
                                                    conv.test_isinstance((basestring, int)),
                                                    drop_none_items=True,
                                                    ),
                                                conv.default([]),
                                                ),
                                            id=conv.pipe(
                                                conv.test_isinstance((basestring, int)),
                                                conv.not_none,
                                                ),
                                            parents=conv.pipe(
                                                conv.test_isinstance(list),
                                                conv.uniform_sequence(
                                                    conv.test_isinstance((basestring, int)),
                                                    drop_none_items=True,
                                                    ),
                                                conv.default([]),
                                                ),
                                            ).iteritems(),
                                        (
                                            (variable_class.__name__, variable_class.json_to_python())
                                            for variable_class in variable_class_by_name.itervalues()
                                            if variable_class.entity is Familles and hasattr(variable_class, 'column_type')
                                            ),
                                        )),
                                    drop_none_values=True,
                                    ),
                                drop_none_items=True,
                                ),
                            conv.default({}),
                            ),
                        individus=conv.pipe(
                            conv.make_item_to_singleton(),
                            conv.test_isinstance(list),
                            conv.uniform_sequence(
                                conv.test_isinstance(dict),
                                drop_none_items=True,
                                ),
                            conv.function(set_entities_json_id),
                            conv.uniform_sequence(
                                conv.struct(
                                    dict(itertools.chain(
                                        dict(
                                            id=conv.pipe(
                                                conv.test_isinstance((basestring, int)),
                                                conv.not_none,
                                                ),
                                            ).iteritems(),
                                        (
                                            (variable_class.__name__, variable_class.json_to_python())
                                            for variable_class in variable_class_by_name.itervalues()
                                            if variable_class.entity is Individus and hasattr(variable_class, 'column_type') and variable_class.name not in (
                                                'idfam', 'idfoy', 'idmen', 'quifam', 'quifoy', 'quimen')
                                            ),
                                        )),
                                    drop_none_values=True,
                                    ),
                                drop_none_items=True,
                                ),
                            conv.empty_to_none,
                            conv.not_none,
                            ),
                        ),
                    ),
                )(value, state=state)
            if error is not None:
                return test_case, error

            # Second validation step
            familles_individus_id = [individu['id'] for individu in test_case['individus']]
            test_case, error = conv.struct(
                dict(
                    familles=conv.uniform_sequence(
                        conv.struct(
                            dict(
                                enfants=conv.uniform_sequence(conv.test_in_pop(familles_individus_id)),
                                parents=conv.uniform_sequence(conv.test_in_pop(familles_individus_id)),
                                ),
                            default=conv.noop,
                            ),
                        ),
                    ),
                default=conv.noop,
                )(test_case, state=state)

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

entities = [Familles, Individus]
path_to_root_params = os.path.join(openfisca_core_dir, 'openfisca_core', 'tests', 'assets', 'param_root.xml')
path_to_crds_params = os.path.join(openfisca_core_dir, 'openfisca_core', 'tests', 'assets', 'param_more.xml')


class DummyTaxBenefitSystem(TaxBenefitSystem):
    def __init__(self):
        TaxBenefitSystem.__init__(self, entities)

        self.add_variable_classes_from_file(__file__)
        self.add_legislation_params(path_to_root_params)
        self.add_legislation_params(path_to_crds_params, 'csg.activite')
