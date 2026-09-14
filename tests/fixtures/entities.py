import pytest

from openfisca_core.entities import Entity

from .variables import TestVariable


class TestEntity(Entity):
    def get_variable(
        self,
        variable_name: str,
        check_existence: bool = False,
    ) -> TestVariable:
        result = TestVariable(self)
        result.name = variable_name
        return result

    def check_variable_defined_for_entity(self, variable_name: str) -> bool:
        return True


class TestGroupEntity(Entity):
    def get_variable(
        self,
        variable_name: str,
        check_existence: bool = False,
    ) -> TestVariable:
        result = TestVariable(self)
        result.name = variable_name
        return result

    def check_variable_defined_for_entity(self, variable_name: str) -> bool:
        return True


@pytest.fixture
def persons():
    return TestEntity("person", "persons", "", "")


@pytest.fixture
def households(persons):
    roles = [
        {"key": "adult", "plural": "adults", "max": 2},
        {"key": "child", "plural": "children"},
    ]

    group = TestGroupEntity("household", "households", "", "")
    group.add_roles(persons, roles)
    return group
