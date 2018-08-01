# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from nose.tools import raises

from openfisca_core.json_to_test_case import check_entities_and_role
from openfisca_core.taxbenefitsystems import VariableNotFound

from .test_countries import tax_benefit_system


@raises(ValueError)
def test_all_keys_must_be_valid_entity_names():
    test_case = {'unknown_entity': [{'id': 0, 'salary': 1}]}
    test_case = check_entities_and_role(test_case, tax_benefit_system, None)


@raises(ValueError)
def test_entities_lists_must_be_singleton_or_list_of_objects():
    test_case = {'persons': [[], []], 'households': [{'parents': ['0']}]}
    test_case = check_entities_and_role(test_case, tax_benefit_system, None)


def test_ids_should_be_added_to_test_entities():
    test_case = {'persons': [{'id': 0, 'salary': 1}], 'households': [{'parents': ['0']}]}
    test_case = check_entities_and_role(test_case, tax_benefit_system, None)
    assert test_case['households'][0].get('id') is not None


@raises(ValueError)
def test_ids_must_not_be_set_to_None():
    test_case = {'persons': [{'id': None, 'salary': 1}], 'households': [{'id': None}]}
    test_case = check_entities_and_role(test_case, tax_benefit_system, None)


@raises(ValueError)
def test_ids_must_be_strings_or_ints():
    test_case = {'persons': [{'id': 0, 'salary': 1}], 'households': [{'id': {}}]}
    test_case = check_entities_and_role(test_case, tax_benefit_system, None)


@raises(ValueError)
def test_entity_members_must_be_singleton_or_list():
    test_case = {'persons': [{'id': 0, 'salary': 1}], 'households': [{'parents': {}}]}
    test_case = check_entities_and_role(test_case, tax_benefit_system, None)


def test_entity_members_multiple_roles_should_be_casted_to_a_list():
    test_case = {'persons': [{'id': 0, 'salary': 1}], 'households': [{'parents': 0}]}
    test_case = check_entities_and_role(test_case, tax_benefit_system, None)
    assert test_case['households'][0]['parents'] == [0]


@raises(ValueError)
def test_variables_must_be_set_for_the_right_entity():
    test_case = {'persons': [{'id': 0}], 'households': [{'parents': 0, 'salary': 1}]}
    test_case = check_entities_and_role(test_case, tax_benefit_system, None)


@raises(ValueError)
def test_variables_values_must_be_valid():
    test_case = {'persons': [{'id': 0, 'salary': {"nonsense": 10000}}], 'households': [{'parents': 0}]}
    test_case = check_entities_and_role(test_case, tax_benefit_system, None)


@raises(VariableNotFound)
def test_variables_must_exist_in_tbs():
    test_case = {'persons': [{'id': 0, 'salarrry': 1}], 'households': [{'parents': 0}]}
    test_case = check_entities_and_role(test_case, tax_benefit_system, None)


def test_all_entities_should_be_set():
    test_case = {'persons': [{'id': 0, 'salary': 1}]}
    test_case = check_entities_and_role(test_case, tax_benefit_system, None)
    assert test_case['households'] is not None
