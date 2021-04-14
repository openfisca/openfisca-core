import pytest

from openfisca_core.entities import Entity, GroupEntity

from .variables import TestVariable


class TestEntity(Entity):
    def get_variable(self, variable_name):
        result = TestVariable(self)
        result.name = variable_name
        return result

    def check_variable_defined_for_entity(self, variable_name):
        return True


class TestGroupEntity(GroupEntity):
    def get_variable(self, variable_name):
        result = TestVariable(self)
        result.name = variable_name
        return result

    def check_variable_defined_for_entity(self, variable_name):
        return True


@pytest.fixture
def persons():
    return TestEntity("person", "persons", "", "")


@pytest.fixture
def households():
    roles = [{
        'key': 'parent',
        'plural': 'parents',
        'max': 2
        }, {
        'key': 'child',
        'plural': 'children'
        }]

    return TestGroupEntity("household", "households", "", "", roles)
