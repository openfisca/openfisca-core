import os
from typing import List

import pytest
import numpy as np

from openfisca_core.tools.test_runner import _get_tax_benefit_system, YamlItem
from openfisca_core.errors import VariableNotFound
from openfisca_core.variables import Variable
from openfisca_core.populations import Population
from openfisca_core.entities import Entity
from openfisca_core.periods import ETERNITY


class TaxBenefitSystem:
    def __init__(self):
        self.variables = {'salary': MyVariable()}
        self.person_entity = Entity('person', 'persons', None, "")
        self.person_entity.set_tax_benefit_system(self)

    @staticmethod
    def get_package_metadata():
        return {"name": "Test", "version": "Test"}

    def apply_reform(self, _path):
        return Reform(self)

    @staticmethod
    def load_extension(_extension):
        pass

    @staticmethod
    def entities_by_singular():
        return {}

    @staticmethod
    def entities_plural():
        return {}

    def instantiate_entities(self):
        return {'person': Population(self.person_entity)}

    def get_variable(self, variable_name, check_existence = False):
        return self.variables.get(variable_name, check_existence)

    @staticmethod
    def clone():
        return TaxBenefitSystem()


class Reform(TaxBenefitSystem):
    def __init__(self, baseline):
        super().__init__()
        self.baseline = baseline


class Simulation:
    def __init__(self):
        self.populations = {"person": None}

    @staticmethod
    def get_population(plural = None):
        return None


class MyFile:

    def __init__(self):
        self.config = None
        self.nodeid = 'testname'
        self.session = None


class MyItem(YamlItem):
    def __init__(self, test):
        super().__init__('', MyFile(), TaxBenefitSystem(), test, {})

        self.tax_benefit_system = self.baseline_tax_benefit_system
        self.simulation = Simulation()


class MyVariable(Variable):
    definition_period = ETERNITY
    entity = Entity('person', 'persons', None, "")
    value_type = float

    def __init__(self):
        super().__init__()
        self.end = None
        self.is_neutralized = False
        self.set_input = None
        self.dtype = np.float32


def test_variable_not_found():
    test = {"output": {"unknown_variable": 0}}
    with pytest.raises(VariableNotFound) as excinfo:
        test_item = MyItem(test)
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
    test_item = MyItem(test)
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
    test_item = MyItem(test)
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
