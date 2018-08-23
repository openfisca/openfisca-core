# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
from http.client import OK
from nose.tools import assert_equal
import json
from . import subject


entities_response = subject.get('/entities')

# /entities


def test_return_code():
    assert_equal(entities_response.status_code, OK)


def test_response_data():
    entities = json.loads(entities_response.data.decode('utf-8'))
    test_description = '''
Household is an example of a group entity.
A group entity contains one or more individual·s.
Each individual in a group entity has a role (e.g. parent or children). Some roles can only be held by a limited number of individuals (e.g. a 'first_parent' can only be held by one individual), while others can have an unlimited number of individuals (e.g. 'children').

Example:
Housing variables (e.g. housing_tax') are usually defined for a group entity such as 'Household'.

Usage:
Check the number of individuals of a specific role (e.g. check if there is a 'second_parent' with household.nb_persons(Household.SECOND_PARENT)).
Calculate a variable applied to each individual of the group entity (e.g. calculate the 'salary' of each member of the 'Household' with salaries = household.members('salary', period = MONTH); sum_salaries = household.sum(salaries)).

For more information, see: https://openfisca.org/doc/coding-the-legislation/50_entities.html
'''
    assert_equal(
        entities['household'],
        {
            'description': test_description,
            'plural': 'households'
         }
        )
