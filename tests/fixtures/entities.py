import pytest

from openfisca_core.entities import Entity, GroupEntity

from .variables import FixtureVariable


class FixtureEntity(Entity):
    def get_variable(self, variable_name, __arg = None):
        result = FixtureVariable(self)
        result.name = variable_name
        return result

    def check_variable_defined_for_entity(self, variable_name):
        return True


class FixtureGroupEntity(GroupEntity):
    def get_variable(self, variable_name, __arg = None):
        result = FixtureVariable(self)
        result.name = variable_name
        return result

    def check_variable_defined_for_entity(self, variable_name):
        return True


@pytest.fixture
def persons():
    return FixtureEntity("person", "persons", "", "")


@pytest.fixture
def households():
    roles = [{
        "key": "parent",
        "plural": "parents",
        "max": 2
        }, {
        "key": "child",
        "plural": "children"
        }]

    return FixtureGroupEntity("household", "households", "", "", roles)
