# -*- coding: utf-8 -*-

from nose.tools import raises

from openfisca_core.json_to_test_case import check_entities_and_role

from test_countries import tax_benefit_system


def test_ids_should_be_added_to_test_entities():
    test_case = {'individus': [{'id': 0, 'salaire_brut': 1}], 'familles': [{'parents': ['0']}]}
    test_case, error = check_entities_and_role(test_case, tax_benefit_system, None)
    assert error is None
    assert test_case['familles'][0].get('id') is not None

# @raises(ValueError)
def test_ids_must_not_be_set_to_None():
    test_case = {'individus': [{'id': None, 'salaire_brut': 1}], 'familles': [{'id': None}]}
    test_case, error = check_entities_and_role(test_case, tax_benefit_system, None)
    assert error is not None


def test_ids_must_not_be_strings_or_ints():
    test_case = {'individus': [{'id': 0, 'salaire_brut': 1}], 'familles': [{'id': {}}]}
    test_case, error = check_entities_and_role(test_case, tax_benefit_system, None)
    assert error is not None


def test_entity_members_must_be_singleton_or_list():
    test_case = {'individus': [{'id': 0, 'salaire_brut': 1}], 'familles': [{'parents': {}}]}
    test_case, error = check_entities_and_role(test_case, tax_benefit_system, None)
    assert error is not None


def test_entity_members_multiple_roles_should_be_casted_to_a_list():
    test_case = {'individus': [{'id': 0, 'salaire_brut': 1}], 'familles': [{'parents': 0}]}
    test_case, error = check_entities_and_role(test_case, tax_benefit_system, None)
    assert test_case['familles'][0]['parents'] == [0]
