import pytest

from openfisca_core.entities import Entity, GroupEntity

from .variables import TestVariable


class TestEntity(Entity):
    @property
    def variables(self):
        return self

    def exists(self):
        return self

    def isdefined(self):
        return self

    def get(self, variable_name):
        result = TestVariable(self)
        result.name = variable_name
        return result


class TestGroupEntity(GroupEntity):
    @property
    def variables(self):
        return self

    def exists(self):
        return self

    def isdefined(self):
        return self

    def get(self, variable_name):
        result = TestVariable(self)
        result.name = variable_name
        return result


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
