# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
import json

from numpy import unicode_
from nose.tools import assert_equal, assert_is_instance
from http.client import OK
import dpath

from openfisca_core.model_api import Variable
from openfisca_core.periods import MONTH

from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_country_template.entities import Person
from openfisca_country_template.situation_examples import single, couple

from . import subject


def assert_items_equal(x, y):
    assert_equal(set(x), set(y))


def test_trace_basic():
    simulation_json = json.dumps(single)
    response = subject.post('/trace', data = simulation_json, content_type = 'application/json')
    assert_equal(response.status_code, OK)
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


class variable__str_with_max(Variable):
    value_type = str
    max_length = 5
    entity = Person
    definition_period = MONTH
    label = "String variable of specific max length"


def new_simulation(tax_benefit_system, month):
    return tax_benefit_system.new_scenario().init_from_attributes(
        period = month,
        input_variables = dict(
            ),
        ).new_simulation()


def test_variable__str_with_max():
    month = '2018-01'
    tax_benefit_system = CountryTaxBenefitSystem()
    tax_benefit_system.add_variable(variable__str_with_max)
    simulation = new_simulation(tax_benefit_system, month)
    variable_value = simulation.calculate('variable__str_with_max', month)[0]
    assert_equal(unicode_, type(variable_value))
