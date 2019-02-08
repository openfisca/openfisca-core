from openfisca_core.tools.test_runner import _run_test, _get_tax_benefit_system
from openfisca_core.errors import VariableNotFound


import pytest


class TaxBenefitSystem:
    def __init__(self):
        self.variables = {}

    def get_package_metadata(self):
        return {"name": "Test", "version": "Test"}

    def apply_reform(self, path):
        return Reform(self)


class Reform(TaxBenefitSystem):
    def __init__(self, baseline):
        self.baseline = baseline


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


class reform_ab(Reform):
    def apply(self):
        self.key = self.__class__.__name__


class reform_ba(Reform):
    def apply(self):
        self.key = self.__class__.__name__


def test_tax_benefit_systems_with_reform_cache():
    baseline = TaxBenefitSystem()
    extensions = []
    
    ab_tax_benefit_system = _get_tax_benefit_system(baseline, 'ab', extensions)
    ba_tax_benefit_system = _get_tax_benefit_system(baseline, 'ba', extensions)
    assert ab_tax_benefit_system != ba_tax_benefit_system
