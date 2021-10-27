from __future__ import annotations

from typing import Sequence

from openfisca_core.types import TaxBenefitSystemType

import os
import sys
import textwrap

from pytest import File, Item

from openfisca_core.errors import SituationParsingError, VariableNotFoundError
from openfisca_core.simulations import SimulationBuilder

from . import _asserts
from . import _misc

from ._options_schema import _OptionsSchema
from ._test_schema import _TestSchema

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

    name: str = ""
    test: _TestSchema

    def __init__(
            self,
            name: str,
            parent: File,
            baseline_tax_benefit_system: TaxBenefitSystemType,
            test: _TestSchema,
            options: _OptionsSchema,
            ) -> None:

        super(YamlItem, self).__init__(name, parent)
        self.baseline_tax_benefit_system = baseline_tax_benefit_system
        self.options = options
        self.test = test
        self.simulation = None
        self.tax_benefit_system = None

    def runtest(self) -> None:
        extensions: Sequence[str] = []
        reforms: Sequence[str] = []

        if "name" in self.test:
            self.name = self.test["name"]

        if "output" not in self.test:
            raise ValueError("Missing key 'output' in test '{}' in file '{}'".format(self.name, self.fspath))

        if not TEST_KEYWORDS.issuperset(self.test.keys()):
            unexpected_keys = set(self.test.keys()).difference(TEST_KEYWORDS)
            raise ValueError("Unexpected keys {} in test '{}' in file '{}'".format(unexpected_keys, self.name, self.fspath))

        if "extensions" in self.test:
            extensions = self.test["extensions"]

        if "reforms" in self.test:
            reforms = self.test["reforms"]

        self.tax_benefit_system = _misc._get_tax_benefit_system(self.baseline_tax_benefit_system, reforms, extensions)

        builder = SimulationBuilder()
        input = self.test.get('input', {})
        period = self.test.get('period')
        max_spiral_loops = self.test.get('max_spiral_loops')
        verbose = self.options.get('verbose')
        performance_graph = self.options.get('performance_graph')
        performance_tables = self.options.get('performance_tables')

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
                self.print_computation_log(tracer)
            if performance_graph:
                self.generate_performance_graph(tracer)
            if performance_tables:
                self.generate_performance_tables(tracer)

    def print_computation_log(self, tracer):
        print("Computation log:")  # noqa T001
        tracer.print_computation_log()

    def generate_performance_graph(self, tracer):
        tracer.generate_performance_graph('.')

    def generate_performance_tables(self, tracer):
        tracer.generate_performance_tables('.')

    def check_output(self):
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

    def check_variable(self, variable_name, expected_value, period, entity_index = None):
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

    def should_ignore_variable(self, variable_name):
        only_variables = self.options.get('only_variables')
        ignore_variables = self.options.get('ignore_variables')
        variable_ignored = ignore_variables is not None and variable_name in ignore_variables
        variable_not_tested = only_variables is not None and variable_name not in only_variables

        return variable_ignored or variable_not_tested

    def repr_failure(self, excinfo):
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
