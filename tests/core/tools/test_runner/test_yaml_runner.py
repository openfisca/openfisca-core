from openfisca_core.tools.test_runner import _get_tax_benefit_system, YamlItem
from openfisca_core.errors import VariableNotFound


import pytest


class TaxBenefitSystem:
    def __init__(self):
        self.variables = {}

    def get_package_metadata(self):
        return {"name": "Test", "version": "Test"}

    def apply_reform(self, path):
        return Reform(self)

    def load_extension(self, extension):
        pass

    def clone(self):
        return TaxBenefitSystem()


class Reform(TaxBenefitSystem):
    def __init__(self, baseline):
        self.baseline = baseline


class Simulation:
    def __init__(self):
        self.populations = {}

    def get_population(self, plural = None):
        return None


class TestItem(YamlItem):
    def __init__(self, test):
        self.test = test
        self.simulation = Simulation()
        self.tax_benefit_system = TaxBenefitSystem()


def test_variable_not_found():
    test = {"output": {"unknown_variable": 0}}
    with pytest.raises(VariableNotFound) as excinfo:
        test_item = TestItem(test)
        test_item.check_output()
    assert excinfo.value.variable_name == "unknown_variable"


def test_tax_benefit_systems_with_reform_cache():
    baseline = TaxBenefitSystem()

    ab_tax_benefit_system = _get_tax_benefit_system(baseline, 'ab', [])
    ba_tax_benefit_system = _get_tax_benefit_system(baseline, 'ba', [])
    assert ab_tax_benefit_system != ba_tax_benefit_system


def test_reforms_formats():
    baseline = TaxBenefitSystem()

    lonely_reform_tbs = _get_tax_benefit_system(baseline, 'lonely_reform', [])
    list_lonely_reform_tbs = _get_tax_benefit_system(baseline, ['lonely_reform'], [])
    assert lonely_reform_tbs == list_lonely_reform_tbs


def test_reforms_order():
    baseline = TaxBenefitSystem()

    abba_tax_benefit_system = _get_tax_benefit_system(baseline, ['ab', 'ba'], [])
    baab_tax_benefit_system = _get_tax_benefit_system(baseline, ['ba', 'ab'], [])
    assert abba_tax_benefit_system != baab_tax_benefit_system  # keep reforms order in cache


def test_tax_benefit_systems_with_extensions_cache():
    baseline = TaxBenefitSystem()

    xy_tax_benefit_system = _get_tax_benefit_system(baseline, [], 'xy')
    yx_tax_benefit_system = _get_tax_benefit_system(baseline, [], 'yx')
    assert xy_tax_benefit_system != yx_tax_benefit_system


def test_extensions_formats():
    baseline = TaxBenefitSystem()

    lonely_extension_tbs = _get_tax_benefit_system(baseline, [], 'lonely_extension')
    list_lonely_extension_tbs = _get_tax_benefit_system(baseline, [], ['lonely_extension'])
    assert lonely_extension_tbs == list_lonely_extension_tbs


def test_extensions_order():
    baseline = TaxBenefitSystem()

    xy_tax_benefit_system = _get_tax_benefit_system(baseline, [], ['x', 'y'])
    yx_tax_benefit_system = _get_tax_benefit_system(baseline, [], ['y', 'x'])
    assert xy_tax_benefit_system == yx_tax_benefit_system  # extensions order is ignored in cache
