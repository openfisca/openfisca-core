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


@pytest.fixture
def persons():
    return TestEntity("person", "persons", "", "")


@pytest.fixture
def households(persons):
    roles = [
        {"key": "adult", "plural": "adults", "max": 2},
        {"key": "child", "plural": "children"},
    ]

    group = TestEntity("household", "households", "", "")
    group.add_relationship(persons, roles)
    return group
