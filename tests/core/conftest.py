# -*- coding: utf-8 -*-

from pytest import fixture

from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_country_template.entities import *  # noqa analysis:ignore

from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_core.tools.test_runner import yaml
from openfisca_core.variables import Variable
from openfisca_core.periods import ETERNITY
from openfisca_core.entities import Entity, GroupEntity
from openfisca_core.model_api import *  # noqa analysis:ignore


# PERIODS

@fixture
def period():
    return "2016-01"


# ENTITIES


class TestVariable(Variable):
    definition_period = ETERNITY
    value_type = float

    def __init__(self, entity):
        self.__class__.entity = entity
        super().__init__()


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

# TAX BENEFIt SYSTEMS


@fixture
def tax_benefit_system():
    return CountryTaxBenefitSystem()


# SIMULATIONS


@fixture
def simulation_builder():
    return SimulationBuilder()


@fixture
def simulation(tax_benefit_system, simulation_builder):
    return SimulationBuilder().build_default_simulation(tax_benefit_system)


@fixture
def make_simulation_from_entities(tax_benefit_system, simulation_builder):
    def _make_simulation_from_entities(entities):
        return simulation_builder.build_from_entities(tax_benefit_system, entities)
    return _make_simulation_from_entities


@fixture
def make_simulation_from_tbs_and_variables(simulation_builder, period):
    def _make_simulation_from_variables_and_tbs(tbs, variables):
        simulation_builder.default_period = period
        return simulation_builder.build_from_variables(tbs, variables)
    return _make_simulation_from_variables_and_tbs


@fixture
def make_simulation_from_yaml(tax_benefit_system, simulation_builder):
    def _make_simulation_from_yaml(simulation_yaml):
        return simulation_builder.build_from_dict(tax_benefit_system, yaml.safe_load(simulation_yaml))
    return _make_simulation_from_yaml


@fixture
def simulation_single(make_simulation_from_entities, single):
    return make_simulation_from_entities(single)


@fixture
def simulation_couple(make_simulation_from_entities, couple):
    return make_simulation_from_entities(couple)


# VARIABLES


@fixture
def make_variable():
    def _make_variable(name, **new_methods_and_attrs):
        methods_and_attrs = {}
        default = dict(value_type = int, entity = Person, definition_period = MONTH)
        methods_and_attrs.update(default)
        methods_and_attrs.update(new_methods_and_attrs)
        return type(name, (Variable, ), methods_and_attrs)
    return _make_variable
