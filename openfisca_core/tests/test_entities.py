# -*- coding: utf-8 -*-

from copy import deepcopy

from openfisca_core.tools import assert_near
from dummy_country.entities import Famille, Individu
from test_countries import tax_benefit_system

TEST_CASE = {
    'individus': [{'id': 'ind0'}, {'id': 'ind1'}, {'id': 'ind2'}, {'id': 'ind3'}, {'id': 'ind4'}, {'id': 'ind5'}],
    'familles': [
        {'enfants': ['ind2', 'ind3'], 'parents': ['ind0', 'ind1']},
        {'enfants': ['ind5'], 'parents': ['ind4']}
        ],
    }

TEST_CASE_AGES = deepcopy(TEST_CASE)
AGES = [40, 37, 7, 9, 54, 20]
for (individu, age) in zip(TEST_CASE_AGES['individus'], AGES):
        individu['age'] = age

DEMANDEUR = Famille.DEMANDEUR
CONJOINT = Famille.CONJOINT
PARENT = Famille.PARENT
ENFANT = Famille.ENFANT


def new_simulation(test_case):
    return tax_benefit_system.new_scenario().init_from_test_case(
        period = 2013,
        test_case = test_case
        ).new_simulation()


def test_role_index_and_positions():
    simulation = new_simulation(TEST_CASE)
    assert((simulation.famille.members_role == [DEMANDEUR, CONJOINT, ENFANT, ENFANT, DEMANDEUR, ENFANT]).all())
    assert_near(simulation.famille.members_legacy_role, [0, 1, 2, 3, 0, 2])
    assert_near(simulation.famille.members_entity_id, [0, 0, 0, 0, 1, 1])
    assert_near(simulation.famille.members_position, [0, 1, 2, 3, 0, 1])


def test_has_role():
    simulation = new_simulation(TEST_CASE)
    individu = simulation.persons
    assert_near(individu.has_role(ENFANT), [False, False, True, True, False, True])


def test_has_role_with_subrole():
    simulation = new_simulation(TEST_CASE)
    individu = simulation.persons
    assert_near(individu.has_role(PARENT), [True, True, False, False, True, False])
    assert_near(individu.has_role(DEMANDEUR), [True, False, False, False, True, False])
    assert_near(individu.has_role(CONJOINT), [False, True, False, False, False, False])


def test_project():
    test_case = deepcopy(TEST_CASE)
    test_case['familles'][0]['af'] = 20000

    simulation = new_simulation(test_case)
    famille = simulation.famille

    af = famille('af', 2013)
    af_projete = famille.project(af)

    assert_near(af_projete, [20000, 20000, 20000, 20000, 0, 0])

    af_projete_parents = famille.project(af, role = PARENT)
    assert_near(af_projete_parents, [20000, 20000, 0, 0, 0, 0])


def test_implicit_projection():
    test_case = deepcopy(TEST_CASE)
    test_case['familles'][0]['af'] = 20000

    simulation = new_simulation(test_case)
    individu = simulation.get_entity(Individu)
    af = individu.famille('af')

    assert_near(af, [20000, 20000, 20000, 20000, 0, 0])


def test_project_on_first_person():
    test_case = deepcopy(TEST_CASE)
    test_case['familles'][0]['af'] = 20000
    test_case['familles'][1]['af'] = 5000

    simulation = new_simulation(test_case)
    famille = simulation.famille

    af = famille('af')
    af_projete = famille.project_on_first_person(af)

    assert_near(af_projete, [20000, 0, 0, 0, 5000, 0])


def test_share_between_members():
    test_case = deepcopy(TEST_CASE)
    test_case['familles'][0]['af'] = 20000
    test_case['familles'][1]['af'] = 5000

    simulation = new_simulation(test_case)
    famille = simulation.famille

    af = famille('af')

    af_shared = famille.share_between_members(af, role = PARENT)

    assert_near(af_shared, [10000, 10000, 0, 0, 5000, 0])


def test_sum():
    test_case = deepcopy(TEST_CASE)
    test_case['individus'][0]['salaire_net'] = 1000
    test_case['individus'][1]['salaire_net'] = 1500
    test_case['individus'][4]['salaire_net'] = 3000
    test_case['individus'][5]['salaire_net'] = 500

    simulation = new_simulation(test_case)
    famille = simulation.famille

    salaire_net = famille.members('salaire_net')
    salaire_total_par_famille = famille.sum(salaire_net)

    assert_near(salaire_total_par_famille, [2500, 3500])

    salaire_total_parents_par_famille = famille.sum(salaire_net, role = PARENT)

    assert_near(salaire_total_parents_par_famille, [2500, 3000])


def test_any():
    test_case = deepcopy(TEST_CASE_AGES)
    simulation = new_simulation(test_case)
    famille = simulation.famille

    age = famille.members('age')
    condition_age = (age <= 18)
    has_famille_member_with_age_inf_18 = famille.any(condition_age)
    assert_near(has_famille_member_with_age_inf_18, [True, False])

    condition_age_2 = (age > 18)
    has_famille_enfant_with_age_sup_18 = famille.any(condition_age_2, role = ENFANT)
    assert_near(has_famille_enfant_with_age_sup_18, [False, True])


def test_all():
    test_case = deepcopy(TEST_CASE_AGES)
    simulation = new_simulation(test_case)
    famille = simulation.famille

    age = famille.members('age')

    condition_age = (age >= 18)
    all_persons_age_sup_18 = famille.all(condition_age)
    assert_near(all_persons_age_sup_18, [False, True])

    all_parents_age_sup_18 = famille.all(condition_age, role = PARENT)
    assert_near(all_parents_age_sup_18, [True, True])


def test_max():
    test_case = deepcopy(TEST_CASE_AGES)
    simulation = new_simulation(test_case)
    famille = simulation.famille

    age = famille.members('age')

    age_max = famille.max(age)
    assert_near(age_max, [40, 54])

    age_max_enfants = famille.max(age, role = ENFANT)
    assert_near(age_max_enfants, [9, 20])


def test_min():
    test_case = deepcopy(TEST_CASE_AGES)
    simulation = new_simulation(test_case)
    famille = simulation.famille

    age = famille.members('age')

    age_min = famille.min(age)
    assert_near(age_min, [7, 20])

    age_min_parents = famille.min(age, role = PARENT)
    assert_near(age_min_parents, [37, 54])


def test_partner():
    test_case = deepcopy(TEST_CASE)
    test_case['individus'][0]['salaire_net'] = 1000
    test_case['individus'][1]['salaire_net'] = 1500
    test_case['individus'][4]['salaire_net'] = 3000
    test_case['individus'][5]['salaire_net'] = 500

    simulation = new_simulation(test_case)
    individus = simulation.get_entity(Individu)

    salaire_net = individus('salaire_net')

    salaire_conjoint = individus.value_from_partner(salaire_net, individus.famille, PARENT)

    assert_near(salaire_conjoint, [1500, 1000, 0, 0, 0, 0])


def test_value_from_first_person():
    test_case = deepcopy(TEST_CASE)
    test_case['individus'][0]['salaire_net'] = 1000
    test_case['individus'][1]['salaire_net'] = 1500
    test_case['individus'][4]['salaire_net'] = 3000
    test_case['individus'][5]['salaire_net'] = 500

    simulation = new_simulation(test_case)
    famille = simulation.famille

    salaires_net = famille.members('salaire_net')
    salaire_first_person = famille.value_from_first_person(salaires_net)

    assert_near(salaire_first_person, [1000, 3000])


def test_sum_following_bug_ipp_1():
    test_case = {
        'individus': [{'id': 'ind0'}, {'id': 'ind1'}, {'id': 'ind2'}, {'id': 'ind3'}],
        'familles': [
            {'parents': ['ind0']},
            {'parents': ['ind1'], 'enfants': ['ind2', 'ind3']}
            ],
        }
    test_case['individus'][0]['a_charge_fiscale'] = False
    test_case['individus'][1]['a_charge_fiscale'] = False
    test_case['individus'][2]['a_charge_fiscale'] = True
    test_case['individus'][3]['a_charge_fiscale'] = True

    simulation = new_simulation(test_case)
    famille = simulation.famille

    elibible_i = famille.members('a_charge_fiscale')
    nb_a_charge_fiscales_par_famille = famille.sum(elibible_i, role = ENFANT)

    assert_near(nb_a_charge_fiscales_par_famille, [0, 2])


def test_sum_following_bug_ipp_2():
    test_case = {
        'individus': [{'id': 'ind0'}, {'id': 'ind1'}, {'id': 'ind2'}, {'id': 'ind3'}],
        'familles': [
            {'parents': ['ind1'], 'enfants': ['ind2', 'ind3']},
            {'parents': ['ind0']}
            ],
        }
    test_case['individus'][0]['a_charge_fiscale'] = False
    test_case['individus'][1]['a_charge_fiscale'] = False
    test_case['individus'][2]['a_charge_fiscale'] = True
    test_case['individus'][3]['a_charge_fiscale'] = True

    simulation = new_simulation(test_case)
    famille = simulation.famille

    elibible_i = famille.members('a_charge_fiscale')
    nb_eligibles_par_famille = famille.sum(elibible_i, role = ENFANT)

    assert_near(nb_eligibles_par_famille, [2, 0])
