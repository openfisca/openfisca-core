# -*- coding: utf-8 -*-

from enum import Enum
from datetime import date
from pytest import fixture

from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_country_template import CountryTaxBenefitSystem

from openfisca_core.variables import Variable
from openfisca_core.periods import ETERNITY
from openfisca_core.entities import Entity, GroupEntity
from openfisca_country_template.entities import Household
from openfisca_core.indexed_enums import Enum as OFEnum


class TestVariable(Variable):
    definition_period = ETERNITY
    value_type = float

    def __init__(self, entity):
        self.__class__.entity = entity
        super().__init__()


@fixture
def tax_benefit_system():
    return CountryTaxBenefitSystem()


@fixture
def simulation_builder():
    return SimulationBuilder()


@fixture
def period():
    return "2016-01"


@fixture
def make_simulation(tax_benefit_system, simulation_builder, period):
    def _make_simulation(data):
        simulation_builder.default_period = period
        return simulation_builder.build_from_variables(tax_benefit_system, data)
    return _make_simulation


@fixture
def make_isolated_simulation(simulation_builder, period):
    def _make_simulation(tbs, data):
        simulation_builder.default_period = period
        return simulation_builder.build_from_variables(tbs, data)
    return _make_simulation


@fixture
def persons():
    class TestPersonEntity(Entity):
        def get_variable(self, variable_name):
            result = TestVariable(self)
            result.name = variable_name
            return result

        def check_variable_defined_for_entity(self, variable_name):
            return True

    return TestPersonEntity("person", "persons", "", "")


@fixture
def int_variable(persons):

    class intvar(Variable):
        definition_period = ETERNITY
        value_type = int
        entity = persons

        def __init__(self):
            super().__init__()

    return intvar()


@fixture
def date_variable(persons):

    class datevar(Variable):
        definition_period = ETERNITY
        value_type = date
        entity = persons

        def __init__(self):
            super().__init__()

    return datevar()


@fixture
def enum_variable():

    class TestEnum(Variable):
        definition_period = ETERNITY
        value_type = OFEnum
        dtype = 'O'
        default_value = '0'
        is_neutralized = False
        set_input = None
        possible_values = Enum('foo', 'bar')
        name = "enum"

        def __init__(self):
            pass

    return TestEnum()


@fixture
def group_entity():
    class Household(GroupEntity):
        def get_variable(self, variable_name):
            result = TestVariable(self)
            result.name = variable_name
            return result

        def check_variable_defined_for_entity(self, variable_name):
            return True

    roles = [{
        'key': 'parent',
        'plural': 'parents',
        'max': 2
        }, {
        'key': 'child',
        'plural': 'children'
        }]

    return Household("household", "households", "", "", roles)

