from openfisca_core.tools.test_runner import _run_test
from openfisca_core.errors import VariableNotFound


import pytest


class TaxBenefitSystem:
    def __init__(self):
        self.variables = {}

    def get_package_metadata(self):
        return {"name": "Test", "version": "Test"}


class Simulation:
    def __init__(self):
        self.tax_benefit_system = TaxBenefitSystem()
        self.entities = {}

    def get_entity(self, plural = None):
        return None


def test_variable_not_found():
    test = {"output": {"unknown_variable": 0}}
    with pytest.raises(VariableNotFound) as excinfo:
        _run_test(Simulation(), test)
    assert excinfo.value.variable_name == "unknown_variable"
