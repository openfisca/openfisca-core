# -*- coding: utf-8 -*-

from enum import Enum
from datetime import date
from pytest import fixture

from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_country_template.entities import *  # noqa analysis:ignore

from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_core.tools.test_runner import yaml
from openfisca_core.variables import Variable
from openfisca_core.periods import ETERNITY
from openfisca_core.entities import Entity, GroupEntity
from openfisca_core.indexed_enums import Enum as OFEnum
from openfisca_core.model_api import *  # noqa analysis:ignore


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
def simulation(tax_benefit_system, simulation_builder):
    return SimulationBuilder().build_default_simulation(tax_benefit_system)


@fixture
def period():
    return "2016-01"


@fixture
def year_period():
    return "2016"


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
def make_simulation_from_yaml(tax_benefit_system, simulation_builder):
    def _make_simulation_from_yaml(simulation_yaml):
        return simulation_builder.build_from_dict(tax_benefit_system, yaml.safe_load(simulation_yaml))
    return _make_simulation_from_yaml


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


@fixture
def single():
    return {
        "persons": {
            "Alicia": {
                "birth": {
                    "2017-01": None
                    },
                "disposable_income": {
                    "2017-01": None
                    }
                }
            },
        "households": {
            "_": {
                "parents": ["Alicia"]
                }
            }
        }


@fixture
def couple():
    return {
    "persons": {
        "Alicia": {
            "birth": {
                "ETERNITY": "1980-01-01"
            },
            "salary": {
                "2017-01": 4000
            },
            "disposable_income": {
                "2017-01": None
            }
        },
        "Javier": {
            "birth": {
                "ETERNITY": "1984-01-01"
            },
            "salary": {
                "2017-01": 2500
            },
            "disposable_income": {
                "2017-01": None
            }
        }
    },
    "households": {
        "_": {
            "parents": ["Alicia", "Javier"],
            "total_benefits": {
                "2017-01": None
            },
            "total_taxes": {
                "2017-01": None
            }
        }
    }
}

@fixture
def simulation_single(simulation_builder, tax_benefit_system, single):
    return simulation_builder.build_from_entities(tax_benefit_system, single)


@fixture
def simulation_couple(simulation_builder, tax_benefit_system, couple):
    return simulation_builder.build_from_entities(tax_benefit_system, couple)


class simple_variable(Variable):
    entity = Person
    definition_period = MONTH
    value_type = int


class variable_with_calculate_output_add(Variable):
    entity = Person
    definition_period = MONTH
    value_type = int
    calculate_output = calculate_output_add


class variable_with_calculate_output_divide(Variable):
    entity = Person
    definition_period = YEAR
    value_type = int
    calculate_output = calculate_output_divide


@fixture
def simulation_single_with_variables(simulation_builder, tax_benefit_system, single):
    tax_benefit_system.add_variables(
        simple_variable,
        variable_with_calculate_output_add,
        variable_with_calculate_output_divide
        )
    return simulation_builder.build_from_entities(tax_benefit_system, single)



# 1 <--> 2 with same period
class variable1(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        return person('variable2', period)


class variable2(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        return person('variable1', period)


# 3 <--> 4 with a period offset
class variable3(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        return person('variable4', period.last_month)


class variable4(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        return person('variable3', period)


# 5 -f-> 6 with a period offset
#   <---
class variable5(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        variable6 = person('variable6', period.last_month)
        return 5 + variable6


class variable6(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        variable5 = person('variable5', period)
        return 6 + variable5


class variable7(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        variable5 = person('variable5', period)
        return 7 + variable5


# december cotisation depending on november value
class cotisation(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        if period.start.month == 12:
            return 2 * person('cotisation', period.last_month)
        else:
            return person.empty_array() + 1


@fixture
def simulation_with_variables(tax_benefit_system, simulation_builder):
    tax_benefit_system.add_variables(variable1, variable2, variable3, variable4,
        variable5, variable6, variable7, cotisation)
    return SimulationBuilder().build_default_simulation(tax_benefit_system)
