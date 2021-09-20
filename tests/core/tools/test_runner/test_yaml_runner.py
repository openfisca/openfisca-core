import os
from typing import List

import pytest
import numpy as np

from openfisca_core.tools.test_runner import _get_tax_benefit_system, YamlItem, YamlFile
from openfisca_core.errors import VariableNotFound
from openfisca_core.variables import Variable
from openfisca_core.populations import Population
from openfisca_core.entities import Entity
from openfisca_core.periods import ETERNITY


class TaxBenefitSystem:
    def __init__(self):
        self.variables = {'salary': TestVariable()}
        self.person_entity = Entity('person', 'persons', None, "")
        self.person_entity.tax_benefit_system = self

    def get_package_metadata(self):
        return {"name": "Test", "version": "Test"}

    def apply_reform(self, path):
        return Reform(self)

    def load_extension(self, extension):
        pass

    def entities_by_singular(self):
        return {}

    def entities_plural(self):
        return {}

    def instantiate_entities(self):
        return {'person': Population(self.person_entity)}

    def get_variable(self, variable_name, check_existence = True):
        return self.variables.get(variable_name)

    def clone(self):
        return TaxBenefitSystem()


class Reform(TaxBenefitSystem):
    def __init__(self, baseline):
        self.baseline = baseline


class Simulation:
    def __init__(self):
        self.populations = {"person": None}

    def get_population(self, plural = None):
        return None


class TestFile(YamlFile):

    def __init__(self):
        self.config = None
        self.session = None
        self._nodeid = 'testname'


class TestItem(YamlItem):
    def __init__(self, test):
        super().__init__('', TestFile(), TaxBenefitSystem(), test, {})

        self.tax_benefit_system = self.baseline_tax_benefit_system
        self.simulation = Simulation()


class TestVariable(Variable):
    definition_period = ETERNITY
    value_type = float

    def __init__(self):
        self.end = None
        self.entity = Entity('person', 'persons', None, "")
        self.is_neutralized = False
        self.set_input = None
        self.dtype = np.float32


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


def test_performance_graph_option_output():
    test = {'input': {'salary': {'2017-01': 2000}}, 'output': {'salary': {'2017-01': 2000}}}
    test_item = TestItem(test)
    test_item.options = {'performance_graph': True}

    paths = ["./performance_graph.html"]

    clean_performance_files(paths)

    test_item.runtest()

    assert test_item.simulation.trace
    for path in paths:
        assert os.path.isfile(path)

    clean_performance_files(paths)


def test_performance_tables_option_output():
    test = {'input': {'salary': {'2017-01': 2000}}, 'output': {'salary': {'2017-01': 2000}}}
    test_item = TestItem(test)
    test_item.options = {'performance_tables': True}

    paths = ["performance_table.csv", "aggregated_performance_table.csv"]

    clean_performance_files(paths)

    test_item.runtest()

    assert test_item.simulation.trace
    for path in paths:
        assert os.path.isfile(path)

    clean_performance_files(paths)


def clean_performance_files(paths: List[str]):
    for path in paths:
        if os.path.isfile(path):
            os.remove(path)
