import pytest

from openfisca_core.entities import Entity, GroupEntity

from .variables import MyVariable


class MyEntity(Entity):
    def get_variable(self, variable_name, __arg = None):
        result = MyVariable(self)
        result.name = variable_name
        return result

    def check_variable_defined_for_entity(self, variable_name):
        return True


class MyGroupEntity(GroupEntity):
    def get_variable(self, variable_name, __arg = None):
        result = MyVariable(self)
        result.name = variable_name
        return result

    def check_variable_defined_for_entity(self, variable_name):
        return True


@pytest.fixture
def persons():
    return MyEntity("person", "persons", "", "")


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

    return MyGroupEntity("household", "households", "", "", roles)
