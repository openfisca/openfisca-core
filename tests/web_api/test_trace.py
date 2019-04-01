# -*- coding: utf-8 -*-

import json
from copy import deepcopy

from nose.tools import assert_is_instance
from http.client import OK
import dpath
from openfisca_country_template.situation_examples import single, couple

from . import subject


def assert_items_equal(x, y):
    assert set(x) == set(y)


def test_trace_basic():
    simulation_json = json.dumps(single)
    response = subject.post('/trace', data = simulation_json, content_type = 'application/json')
    assert response.status_code == OK
    response_json = json.loads(response.data.decode('utf-8'))
    disposable_income_value = dpath.util.get(response_json, 'trace/disposable_income<2017-01>/value')
    assert_is_instance(disposable_income_value, list)
    assert_is_instance(disposable_income_value[0], float)
    disposable_income_dep = dpath.util.get(response_json, 'trace/disposable_income<2017-01>/dependencies')
    assert_items_equal(
        disposable_income_dep,
        ['salary<2017-01>', 'basic_income<2017-01>', 'income_tax<2017-01>', 'social_security_contribution<2017-01>']
        )
    basic_income_dep = dpath.util.get(response_json, 'trace/basic_income<2017-01>/dependencies')
    assert_items_equal(basic_income_dep, ['age<2017-01>'])


def test_entities_description():
    simulation_json = json.dumps(couple)
    response = subject.post('/trace', data = simulation_json, content_type = 'application/json')
    response_json = json.loads(response.data.decode('utf-8'))
    assert_items_equal(
        dpath.util.get(response_json, 'entitiesDescription/persons'),
        ['Javier', "Alicia"]
        )


def test_root_nodes():
    simulation_json = json.dumps(couple)
    response = subject.post('/trace', data = simulation_json, content_type = 'application/json')
    response_json = json.loads(response.data.decode('utf-8'))
    assert_items_equal(
        dpath.util.get(response_json, 'requestedCalculations'),
        ['disposable_income<2017-01>', 'total_benefits<2017-01>', 'total_taxes<2017-01>']
        )


def test_str_variable():
    new_couple = deepcopy(couple)
    new_couple['households']['_']['postal_code'] = {'2017-01': None}
    simulation_json = json.dumps(new_couple)

    response = subject.post('/trace', data = simulation_json, content_type = 'application/json')

    assert response.status_code == OK
