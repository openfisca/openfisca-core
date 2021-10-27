from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence, Set, Union

from openfisca_core.types import TaxBenefitSystemType

import os
import sys
import textwrap

from _pytest._code.code import ExceptionInfo, TerminalRepr
from pytest import File, Item

from openfisca_core.errors import SituationParsingError, VariableNotFoundError
from openfisca_core.simulations import Simulation, SimulationBuilder
from openfisca_core.tracers import FullTracer

from . import _asserts
from . import _misc

from ._options_schema import _OptionsSchema
from ._test_schema import _TestSchema

TEST_KEYWORDS: Set[str]
TEST_KEYWORDS = {
    'absolute_error_margin',
    'description',
    'extensions',
    'ignore_variables',
    'input',
    'keywords',
    'max_spiral_loops',
    'name',
    'only_variables',
    'output',
    'period',
    'reforms',
    'relative_error_margin',
    }


class YamlItem(Item):
    """
    Terminal nodes of the test collection tree.
    """

    baseline_tax_benefit_system: TaxBenefitSystemType
    name: str = ""
    options: _OptionsSchema
    simulation: Simulation
    tax_benefit_system: TaxBenefitSystemType
    test: _TestSchema

    def __init__(
            self,
            name: str,
            parent: File,
            baseline_tax_benefit_system: TaxBenefitSystemType,
            test: _TestSchema,
            options: _OptionsSchema,
            ) -> None:

        super().__init__(name, parent)
        self.baseline_tax_benefit_system = baseline_tax_benefit_system
        self.options = options
        self.test = test

    def runtest(self) -> None:
        builder: SimulationBuilder
        extensions: Sequence[str] = []
        input: Mapping[str, Any] = {}
        max_spiral_loops: Optional[int] = None
        performance_graph: bool = False
        performance_tables: bool = False
        period: Optional[str] = None
        reforms: Sequence[str] = []
        unexpected_keys: Set[str]
        verbose: bool = False

        if "name" in self.test:
            self.name = self.test["name"]

        if "output" not in self.test:
            raise ValueError("Missing key 'output' in test '{}' in file '{}'".format(self.name, self.fspath))

        if not TEST_KEYWORDS.issuperset(self.test.keys()):
            unexpected_keys = set(self.test.keys()).difference(TEST_KEYWORDS)
            raise ValueError("Unexpected keys {} in test '{}' in file '{}'".format(unexpected_keys, self.name, self.fspath))

        if "reforms" in self.test:
            reforms = self.test["reforms"]

        if "extensions" in self.test:
            extensions = self.test["extensions"]

        self.tax_benefit_system = _misc._get_tax_benefit_system(self.baseline_tax_benefit_system, reforms, extensions)

        builder = SimulationBuilder()

        if "input" in self.test:
            input = self.test["input"]

        if "period" in self.test:
            period = self.test["period"]

        if "max_spiral_loops" in self.test:
            max_spiral_loops = self.test["max_spiral_loops"]

        if "verbose" in self.options:
            verbose = self.options["verbose"]

        if "performance_graph" in self.options:
            performance_graph = self.options["performance_graph"]

        if "performance_tables" in self.options:
            performance_tables = self.options["performance_tables"]

        try:
            builder.set_default_period(period)
            self.simulation = builder.build_from_dict(self.tax_benefit_system, input)
        except (VariableNotFoundError, SituationParsingError):
            raise
        except Exception as e:
            error_message = os.linesep.join([str(e), '', f"Unexpected error raised while parsing '{self.fspath}'"])
            raise ValueError(error_message).with_traceback(sys.exc_info()[2]) from e  # Keep the stack trace from the root error

        if max_spiral_loops:
            self.simulation.max_spiral_loops = max_spiral_loops

        try:
            self.simulation.trace = verbose or performance_graph or performance_tables
            self.check_output()
        finally:
            tracer = self.simulation.tracer
            if verbose:
                assert isinstance(tracer, FullTracer)
                self.print_computation_log(tracer)
            if performance_graph:
                assert isinstance(tracer, FullTracer)
                self.generate_performance_graph(tracer)
            if performance_tables:
                assert isinstance(tracer, FullTracer)
                self.generate_performance_tables(tracer)

    def print_computation_log(self, tracer: FullTracer) -> None:
        print("Computation log:")  # noqa T001
        tracer.print_computation_log()

    def generate_performance_graph(self, tracer: FullTracer) -> None:
        tracer.generate_performance_graph('.')

    def generate_performance_tables(self, tracer: FullTracer) -> None:
        tracer.generate_performance_tables('.')

    def check_output(self) -> None:
        output = self.test.get('output')

        if output is None:
            return
        for key, expected_value in output.items():
            if self.tax_benefit_system.get_variable(key):  # If key is a variable
                self.check_variable(key, expected_value, self.test.get('period'))
            elif self.simulation.populations.get(key):  # If key is an entity singular
                for variable_name, value in expected_value.items():
                    self.check_variable(variable_name, value, self.test.get('period'))
            else:
                population = self.simulation.get_population(plural = key)
                if population is not None:  # If key is an entity plural
                    for instance_id, instance_values in expected_value.items():
                        for variable_name, value in instance_values.items():
                            entity_index = population.get_index(instance_id)
                            self.check_variable(variable_name, value, self.test.get('period'), entity_index)
                else:
                    raise VariableNotFoundError(key, self.tax_benefit_system)

    def check_variable(
            self,
            variable_name: str,
            expected_value: Mapping[str, Any],
            period: Optional[str],
            entity_index: Optional[int] = None,
            ) -> None:

        if self.should_ignore_variable(variable_name):
            return
        if isinstance(expected_value, dict):
            for requested_period, expected_value_at_period in expected_value.items():
                self.check_variable(variable_name, expected_value_at_period, requested_period, entity_index)
            return

        actual_value = self.simulation.calculate(variable_name, period)

        if entity_index is not None:
            actual_value = actual_value[entity_index]
        return _asserts.assert_near(
            actual_value,
            expected_value,
            absolute_error_margin = self.test.get('absolute_error_margin'),
            message = f"{variable_name}@{period}: ",
            relative_error_margin = self.test.get('relative_error_margin'),
            )

    def should_ignore_variable(self, variable_name: str) -> bool:
        only_variables = self.options.get('only_variables')
        ignore_variables = self.options.get('ignore_variables')
        variable_ignored = ignore_variables is not None and variable_name in ignore_variables
        variable_not_tested = only_variables is not None and variable_name not in only_variables

        return variable_ignored or variable_not_tested

    def repr_failure(
            self,
            excinfo: ExceptionInfo[BaseException],
            ) -> Union[str, TerminalRepr]:

        if not isinstance(excinfo.value, (AssertionError, VariableNotFoundError, SituationParsingError)):
            return super(YamlItem, self).repr_failure(excinfo)

        message = excinfo.value.args[0]
        if isinstance(excinfo.value, SituationParsingError):
            message = f"Could not parse situation described: {message}"

        return os.linesep.join([
            f"{str(self.fspath)}:",
            f"  Test '{str(self.name)}':",
            textwrap.indent(message, '    ')
            ])
