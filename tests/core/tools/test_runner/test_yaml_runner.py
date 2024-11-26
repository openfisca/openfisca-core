import os

import numpy
import pytest

from openfisca_core import errors
from openfisca_core.entities import Entity
from openfisca_core.periods import DateUnit
from openfisca_core.populations import Population
from openfisca_core.tools.test_runner import YamlFile, YamlItem, _get_tax_benefit_system
from openfisca_core.variables import Variable


class TaxBenefitSystem:
    def __init__(self) -> None:
        self.variables = {"salary": TestVariable()}
        self.person_entity = Entity("person", "persons", None, "")
        self.person_entity.set_tax_benefit_system(self)

    def get_package_metadata(self):
        return {"name": "Test", "version": "Test"}

    def apply_reform(self, path):
        return Reform(self)

    def load_extension(self, extension) -> None:
        pass

    def entities_by_singular(self):
        return {}

    def entities_plural(self):
        return {}

    def instantiate_entities(self):
        return {"person": Population(self.person_entity)}

    def get_variable(self, variable_name: str, check_existence=True):
        return self.variables.get(variable_name)

    def clone(self):
        return TaxBenefitSystem()


class Reform(TaxBenefitSystem):
    def __init__(self, baseline) -> None:
        self.baseline = baseline


class Simulation:
    def __init__(self) -> None:
        self.populations = {"person": None}

    def get_population(self, plural=None) -> None:
        return None


class TestFile(YamlFile):
    def __init__(self) -> None:
        self.config = None
        self.session = None
        self._nodeid = "testname"


class TestItem(YamlItem):
    """
    Mock a YamlItem for tests.

    Usage example:
        testFile = TestFile.from_parent(parent=None)
        test = {
            "input": {...},
            "output": {...},  # noqa RST201
        }
        test_item = TestItem.from_parent(parent=testFile, test=test)

    where 'from_parent' is inherited from pytest.Item through YamlItem
    """

    def __init__(self, test, **kwargs) -> None:
        # get expected 'parent' from kwargs (comes from 'from_parent')
        super().__init__(
            name="",
            path="",
            baseline_tax_benefit_system=TaxBenefitSystem(),
            test=test,
            options={},
            **kwargs,
        )

        self.tax_benefit_system: TaxBenefitSystem = self.baseline_tax_benefit_system


class TestVariable(Variable):
    definition_period = DateUnit.ETERNITY
    value_type = float

    def __init__(self) -> None:
        self.end = None
        self.entity = Entity("person", "persons", None, "")
        self.is_neutralized = False
        self.set_input = None
        self.dtype = numpy.float32


def test_variable_not_found() -> None:
    test_file = TestFile.from_parent(parent=None)
    test = {"output": {"unknown_variable": 0}}
    with pytest.raises(errors.VariableNotFoundError) as excinfo:
        test_item = TestItem.from_parent(parent=test_file, test=test)
        test_item.simulation = Simulation()
        test_item.check_output()
    assert excinfo.value.variable_name == "unknown_variable"


def test_tax_benefit_systems_with_reform_cache() -> None:
    baseline = TaxBenefitSystem()

    ab_tax_benefit_system = _get_tax_benefit_system(baseline, "ab", [])
    ba_tax_benefit_system = _get_tax_benefit_system(baseline, "ba", [])
    assert ab_tax_benefit_system != ba_tax_benefit_system


def test_reforms_formats() -> None:
    baseline = TaxBenefitSystem()

    lonely_reform_tbs = _get_tax_benefit_system(baseline, "lonely_reform", [])
    list_lonely_reform_tbs = _get_tax_benefit_system(baseline, ["lonely_reform"], [])
    assert lonely_reform_tbs == list_lonely_reform_tbs


def test_reforms_order() -> None:
    baseline = TaxBenefitSystem()

    abba_tax_benefit_system = _get_tax_benefit_system(baseline, ["ab", "ba"], [])
    baab_tax_benefit_system = _get_tax_benefit_system(baseline, ["ba", "ab"], [])
    assert (
        abba_tax_benefit_system != baab_tax_benefit_system
    )  # keep reforms order in cache


def test_tax_benefit_systems_with_extensions_cache() -> None:
    baseline = TaxBenefitSystem()

    xy_tax_benefit_system = _get_tax_benefit_system(baseline, [], "xy")
    yx_tax_benefit_system = _get_tax_benefit_system(baseline, [], "yx")
    assert xy_tax_benefit_system != yx_tax_benefit_system


def test_extensions_formats() -> None:
    baseline = TaxBenefitSystem()

    lonely_extension_tbs = _get_tax_benefit_system(baseline, [], "lonely_extension")
    list_lonely_extension_tbs = _get_tax_benefit_system(
        baseline,
        [],
        ["lonely_extension"],
    )
    assert lonely_extension_tbs == list_lonely_extension_tbs


def test_extensions_order() -> None:
    baseline = TaxBenefitSystem()

    xy_tax_benefit_system = _get_tax_benefit_system(baseline, [], ["x", "y"])
    yx_tax_benefit_system = _get_tax_benefit_system(baseline, [], ["y", "x"])
    assert (
        xy_tax_benefit_system == yx_tax_benefit_system
    )  # extensions order is ignored in cache


def test_performance_graph_option_output() -> None:
    test_file = TestFile.from_parent(parent=None)
    test = {
        "input": {"salary": {"2017-01": 2000}},
        "output": {"salary": {"2017-01": 2000}},
    }
    test_item = TestItem.from_parent(parent=test_file, test=test)
    test_item.options = {"performance_graph": True}

    paths = ["./performance_graph.html"]

    clean_performance_files(paths)

    test_item.runtest()

    assert test_item.simulation.trace
    for path in paths:
        assert os.path.isfile(path)

    clean_performance_files(paths)


def test_performance_tables_option_output() -> None:
    test_file = TestFile.from_parent(parent=None)
    test = {
        "input": {"salary": {"2017-01": 2000}},
        "output": {"salary": {"2017-01": 2000}},
    }
    test_item = TestItem.from_parent(parent=test_file, test=test)
    test_item.options = {"performance_tables": True}

    paths = ["performance_table.csv", "aggregated_performance_table.csv"]

    clean_performance_files(paths)

    test_item.runtest()

    assert test_item.simulation.trace
    for path in paths:
        assert os.path.isfile(path)

    clean_performance_files(paths)


def test_verbose_option_output(capsys) -> None:
    test_file = TestFile.from_parent(parent=None)

    expected_output_variable = "salary"
    expected_output_date = "2017-01"
    expected_output_value = 2000
    test = {
        "input": {"salary": {"2017-01": 2000}},
        "output": {expected_output_variable: {expected_output_date: expected_output_value}},
    }

    test_item = TestItem.from_parent(parent=test_file, test=test)

    # TestItem init should instantiate the TaxBenefitSystem
    assert test_item.tax_benefit_system.get_variable("salary") is not None

    test_item.options = {"verbose": True}
    test_item.runtest()
    captured = capsys.readouterr()

    # TestItem.runtest should set the trace attribute from the 'verbose' option
    assert test_item.simulation.trace is True

    # TestItem.runtest should run print_computation_log
    assert captured.out != ""
    assert expected_output_variable in captured.out
    assert expected_output_date in captured.out
    assert str(expected_output_value) in captured.out


def clean_performance_files(paths: list[str]) -> None:
    for path in paths:
        if os.path.isfile(path):
            os.remove(path)
