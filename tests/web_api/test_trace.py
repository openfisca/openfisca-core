# -*- coding: utf-8 -*-

import json

from nose.tools import assert_equal, assert_items_equal, assert_is_instance
from httplib import OK
import dpath
from openfisca_country_template.situation_examples import single

from . import subject

def test_trace_basic():
    simulation_json = json.dumps(single)
    response = subject.post('/trace', data = simulation_json, content_type = 'application/json')
    assert_equal(response.status_code, OK)
    response_json = json.loads(response.data)
    disposable_income_value = dpath.util.get(response_json, 'disposable_income<2017-01>/value')
    assert_is_instance(disposable_income_value, list)
    assert_is_instance(disposable_income_value[0], float)
    disposable_income_dep = dpath.util.get(response_json, 'disposable_income<2017-01>/dependencies')
    assert_items_equal(
        disposable_income_dep,
        ['salary<2017-01>', 'basic_income<2017-01>', 'income_tax<2017-01>', 'social_security_contribution<2017-01>']
        )
    basic_income_dep = dpath.util.get(disposable_income_dep, 'basic_income<2017-01>/dependencies')
    assert_items_equal(basic_income_dep, ['age<2017-01>'])
