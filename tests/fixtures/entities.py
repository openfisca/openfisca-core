from __future__ import annotations

import pytest

from openfisca_core.entities import Entity, GroupEntity

from .variables import TestVariable


class TestEntity(Entity):
    def get_variable(
        self,
        variable_name: str,
        check_existence: bool = False,
    ) -> None | TestVariable:
        result = TestVariable(self)
        result.name = variable_name
        return result


class TestGroupEntity(GroupEntity):
    def get_variable(
        self,
        variable_name: str,
        check_existence: bool = False,
    ) -> None | TestVariable:
        result = TestVariable(self)
        result.name = variable_name
        return result


@pytest.fixture
def persons():
    return TestEntity("person", "persons", "", "")


@pytest.fixture
def households():
    roles = [
        {"key": "parent", "plural": "parents", "max": 2},
        {"key": "child", "plural": "children"},
    ]

    return TestGroupEntity("household", "households", "", "", roles)
