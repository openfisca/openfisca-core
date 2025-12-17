# Avoid T201 warning for print statements in this test runner
# flake8: noqa: T201
from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from typing_extensions import Literal, TypedDict

from openfisca_core.types import TaxBenefitSystem

import dataclasses
import os
import pathlib
import sys
import textwrap
import traceback
import warnings

import pytest

from openfisca_core.errors import SituationParsingError, VariableNotFound
from openfisca_core.simulations import SimulationBuilder
from openfisca_core.tools import assert_near
from openfisca_core.warnings import LibYAMLWarning


class Options(TypedDict, total=False):
    aggregate: bool
    ignore_variables: Sequence[str] | None
    max_depth: int
    name_filter: str | None
    only_variables: Sequence[str] | None
    pdb: bool
    performance_graph: bool
    performance_tables: bool
    verbose: bool


@dataclasses.dataclass(frozen=True)
class ErrorMargin:
    __root__: dict[str | Literal["default"], float | None]

    def __getitem__(self, key: str) -> float | None:
        if key in self.__root__:
            return self.__root__[key]

        return self.__root__["default"]


@dataclasses.dataclass
class Test:
    absolute_error_margin: ErrorMargin
    relative_error_margin: ErrorMargin
    name: str = ""
    input: dict[str, float | dict[str, float]] = dataclasses.field(default_factory=dict)
    output: dict[str, float | dict[str, float]] | None = None
    period: str | None = None
    reforms: Sequence[str] = dataclasses.field(default_factory=list)
    keywords: Sequence[str] | None = None
    extensions: Sequence[str] = dataclasses.field(default_factory=list)
    description: str | None = None
    max_spiral_loops: int | None = None


def build_test(params: dict[str, Any]) -> Test:
    for key in ["absolute_error_margin", "relative_error_margin"]:
        value = params.get(key)

        if value is None:
            value = {"default": None}

        elif isinstance(value, (float, int, str)):
            value = {"default": float(value)}

        params[key] = ErrorMargin(value)

    return Test(**params)


def import_yaml():
    import yaml

    try:
        from yaml import CLoader as Loader
    except ImportError:
        message = [
            "libyaml is not installed in your environment.",
            "This can make your test suite slower to run. Once you have installed libyaml, ",
            "run 'pip uninstall pyyaml && pip install pyyaml --no-cache-dir'",
            "so that it is used in your Python environment.",
        ]
        warnings.warn(" ".join(message), LibYAMLWarning, stacklevel=2)
        from yaml import SafeLoader as Loader
    return yaml, Loader


TEST_KEYWORDS = {
    "absolute_error_margin",
    "description",
    "extensions",
    "ignore_variables",
    "input",
    "keywords",
    "max_spiral_loops",
    "name",
    "only_variables",
    "output",
    "period",
    "reforms",
    "relative_error_margin",
}

yaml, Loader = import_yaml()

_tax_benefit_system_cache: dict = {}

options: Options = Options()


def discover_test_files(
    paths: Sequence[str], name_filter: str | None = None
) -> list[str]:
    files = []
    yaml_exts = {".yaml", ".yml"}
    for p in paths:
        p = pathlib.Path(p)
        if p.is_file():
            if p.suffix in yaml_exts:
                files.append(str(p.resolve()))
            elif p.suffix == ".py":
                # keep only test_*.py files
                if p.name.startswith("test_"):
                    files.append(str(p.resolve()))
        elif p.is_dir():
            # collect yaml files
            for ext in yaml_exts:
                for f in p.rglob(f"*{ext}"):
                    files.append(str(f.resolve()))
            # collect only python test files named test_*.py
            for f in p.rglob("test_*.py"):
                files.append(str(f.resolve()))
    if name_filter:
        files = [f for f in files if name_filter in pathlib.Path(f).name]
    return sorted(set(files))


def run_tests_in_parallel(tax_benefit_system, paths, options, num_workers, verbose):
    import json
    import pty
    import select
    import shutil
    import subprocess
    import time

    test_files = discover_test_files(paths, options.get("name_filter"))

    if not test_files:
        print("No test files found")
        return 0

    if num_workers <= 0:
        try:
            import multiprocessing

            num_workers = max(1, multiprocessing.cpu_count() - 1)
        except Exception:
            num_workers = 1

    # Limit workers to number of test files
    num_workers = min(num_workers, len(test_files))

    # Split test files evenly across workers
    batches = [[] for _ in range(num_workers)]
    for i, f in enumerate(test_files):
        batches[i % num_workers].append(f)

    # Remove empty batches
    batches = [b for b in batches if b]
    num_workers = len(batches)

    print(f"Running {len(test_files)} test files across {num_workers} workers...")

    # Prepare environment variables for pytest workers
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    if options.get("country_package"):
        env["OPENFISCA_COUNTRY_PACKAGE"] = options.get("country_package")
    env["OPENFISCA_EXTENSIONS"] = json.dumps(options.get("extensions") or [])
    env["OPENFISCA_REFORMS"] = json.dumps(options.get("reforms") or [])
    env["OPENFISCA_OPTIONS"] = json.dumps(options)

    # Get python executable with fallback
    python_bin = sys.executable or shutil.which("python3") or shutil.which("python")
    if not python_bin:
        print("Error: Could not find Python executable")
        return 1

    procs = []
    fds = []
    outputs = ["" for _ in range(num_workers)]
    worker_info = {}
    start_time = time.time()

    # Launch worker processes
    for idx, batch in enumerate(batches):
        if not batch:
            continue
        master_fd, slave_fd = pty.openpty()
        cmd = [
            python_bin,
            "-m",
            "pytest",
            "-p",
            "openfisca_core.tools.parallel_plugin",
            "--maxfail=1",
            "--disable-warnings",
        ]
        if verbose:
            cmd.append("-vv")
        cmd.extend(batch)
        p = subprocess.Popen(
            cmd, stdout=slave_fd, stderr=subprocess.STDOUT, env=env, close_fds=True
        )
        os.close(slave_fd)
        procs.append((idx, p))
        fds.append((idx, master_fd))

        # Store worker info
        file_names = [os.path.basename(f) for f in batch]
        if len(file_names) <= 3:
            file_str = ", ".join(file_names)
        else:
            file_str = f"{', '.join(file_names[:3])} (+{len(file_names) - 3} more)"

        worker_info[idx] = {
            "files": file_str,
            "batch": batch,
            "start_time": time.time(),
            "status": "running",
        }
        print(f"  Worker {idx}: {file_str}")

    print()

    running = set(i for i, _ in procs)
    exit_codes = {}
    last_update = time.time()

    # Monitor workers
    while running:
        rlist = [fd for (_, fd) in fds]
        readable, _, _ = select.select(rlist, [], [], 0.1)
        for fd in readable:
            for idx2, mfd in fds:
                if mfd == fd:
                    try:
                        chunk = os.read(fd, 4096).decode("utf-8", "replace")
                        outputs[idx2] += chunk
                        if verbose:
                            print(f"[Worker {idx2}] {chunk}", end="", flush=True)
                    except OSError:
                        pass

        # Print progress every 2 seconds
        current_time = time.time()
        if current_time - last_update >= 2.0:
            completed = len(exit_codes)
            total = num_workers
            elapsed = current_time - start_time
            print(
                f"\rProgress: {completed}/{total} workers completed ({elapsed:.1f}s elapsed)",
                end="",
                flush=True,
            )
            last_update = current_time

        for idx2, p in procs:
            if idx2 in running:
                ret = p.poll()
                if ret is not None:
                    exit_codes[idx2] = ret
                    duration = time.time() - worker_info[idx2]["start_time"]
                    worker_info[idx2]["status"] = "passed" if ret == 0 else "failed"
                    worker_info[idx2]["duration"] = duration

                    status_symbol = "✓" if ret == 0 else "✗"
                    status_color = "\033[32m" if ret == 0 else "\033[31m"
                    reset_color = "\033[0m"
                    print(
                        f"\r{status_color}{status_symbol}{reset_color} Worker {idx2}: {worker_info[idx2]['files']} ({duration:.1f}s)"
                    )

                    running.remove(idx2)
                    if ret != 0:
                        # Stop on first failure - terminate all other workers
                        for idx3, p2 in procs:
                            if idx3 in running:
                                try:
                                    p2.terminate()
                                except Exception:
                                    pass
                        running.clear()
                        break

    # Close file descriptors
    for _, fd in fds:
        try:
            os.close(fd)
        except OSError:
            pass

    total_duration = time.time() - start_time
    print()

    # Report failures
    for idx, code in exit_codes.items():
        if code != 0:
            print(f"\n{'=' * 80}")
            print(f"Worker {idx} FAILED")
            print(f"{'=' * 80}")
            print(f"Files: {', '.join(worker_info[idx]['batch'])}")
            print(f"{'=' * 80}")
            print(outputs[idx])
            return 1

    # Success summary
    print(f"{'=' * 80}")
    print("✓ All tests passed!")
    print(
        f"  {len(test_files)} test files across {num_workers} workers in {total_duration:.2f}s"
    )
    print(f"{'=' * 80}")
    return 0


def run_tests(
    tax_benefit_system: TaxBenefitSystem,
    paths: str | Sequence[str],
    options: Options = options,
) -> int:
    """Runs all the YAML tests contained in a file or a directory.

    If ``path`` is a directory, subdirectories will be recursively explored.

    Args:
        tax_benefit_system: the tax-benefit system to use to run the tests.
        paths: A path, or a list of paths, towards the files or directories containing the tests to run. If a path is a directory, subdirectories will be recursively explored.
        options: See more details below.

    Returns:
        The number of successful tests executed.

    Raises:
        :exc:`AssertionError`: if a test does not pass.

    **Testing options**:

    +-------------------------------+-----------+-------------------------------------------+
    | Key                           | Type      | Role                                      |
    +===============================+===========+===========================================+
    | verbose                       | ``bool``  |                                           |
    +-------------------------------+-----------+ See :any:`openfisca_test` options doc     |
    | name_filter                   | ``str``   |                                           |
    +-------------------------------+-----------+-------------------------------------------+

    """
    argv = []
    plugins = [OpenFiscaPlugin(tax_benefit_system, options)]

    if options.get("pdb"):
        argv.append("--pdb")

    if options.get("verbose"):
        argv.append("--verbose")

    if isinstance(paths, str):
        paths = [paths]

    return pytest.main([*argv, *paths], plugins=plugins)


class YamlFile(pytest.File):
    def __init__(self, *, tax_benefit_system, options, **kwargs) -> None:
        super().__init__(**kwargs)
        self.tax_benefit_system = tax_benefit_system
        self.options = options

    def collect(self):
        try:
            tests = yaml.load(open(self.path), Loader=Loader)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError, TypeError):
            message = os.linesep.join(
                [
                    traceback.format_exc(),
                    f"'{self.path}' is not a valid YAML file. Check the stack trace above for more details.",
                ],
            )
            raise ValueError(message)

        if not isinstance(tests, list):
            tests: Sequence[dict] = [tests]

        for test in tests:
            if not self.should_ignore(test):
                yield YamlItem.from_parent(
                    self,
                    name="",
                    baseline_tax_benefit_system=self.tax_benefit_system,
                    test=test,
                    options=self.options,
                )

    def should_ignore(self, test):
        name_filter = self.options.get("name_filter")
        return (
            name_filter is not None
            and name_filter not in os.path.splitext(os.path.basename(self.path))[0]
            and name_filter not in test.get("name", "")
            and name_filter not in test.get("keywords", [])
        )


class YamlItem(pytest.Item):
    """Terminal nodes of the test collection tree."""

    def __init__(self, *, baseline_tax_benefit_system, test, options, **kwargs) -> None:
        super().__init__(**kwargs)
        self.baseline_tax_benefit_system = baseline_tax_benefit_system
        self.options = options
        self.test = build_test(test)
        self.simulation = None
        self.tax_benefit_system = None

    def runtest(self) -> None:
        self.name = self.test.name

        if self.test.output is None:
            msg = f"Missing key 'output' in test '{self.name}' in file '{self.path}'"
            raise ValueError(msg)

        self.tax_benefit_system = _get_tax_benefit_system(
            self.baseline_tax_benefit_system,
            self.test.reforms,
            self.test.extensions,
        )

        builder = SimulationBuilder()
        input = self.test.input
        period = self.test.period
        max_spiral_loops = self.test.max_spiral_loops
        verbose = self.options.get("verbose")
        aggregate = self.options.get("aggregate")
        max_depth = self.options.get("max_depth")
        performance_graph = self.options.get("performance_graph")
        performance_tables = self.options.get("performance_tables")

        try:
            builder.set_default_period(period)
            self.simulation = builder.build_from_dict(self.tax_benefit_system, input)
        except (VariableNotFound, SituationParsingError):
            raise
        except Exception as e:
            error_message = os.linesep.join(
                [str(e), "", f"Unexpected error raised while parsing '{self.path}'"],
            )
            raise ValueError(error_message).with_traceback(
                sys.exc_info()[2],
            ) from e  # Keep the stack trace from the root error

        if max_spiral_loops:
            self.simulation.max_spiral_loops = max_spiral_loops

        try:
            self.simulation.trace = verbose or performance_graph or performance_tables
            self.check_output()
        finally:
            tracer = self.simulation.tracer
            if verbose:
                self.print_computation_log(tracer, aggregate, max_depth)
            if performance_graph:
                self.generate_performance_graph(tracer)
            if performance_tables:
                self.generate_performance_tables(tracer)

    def print_computation_log(self, tracer, aggregate, max_depth) -> None:
        tracer.print_computation_log(aggregate, max_depth)

    def generate_performance_graph(self, tracer) -> None:
        tracer.generate_performance_graph(".")

    def generate_performance_tables(self, tracer) -> None:
        tracer.generate_performance_tables(".")

    def check_output(self) -> None:
        output = self.test.output

        if output is None:
            return
        for key, expected_value in output.items():
            if self.tax_benefit_system.get_variable(key):  # If key is a variable
                self.check_variable(key, expected_value, self.test.period)
            elif self.simulation.populations.get(key):  # If key is an entity singular
                for variable_name, value in expected_value.items():
                    self.check_variable(variable_name, value, self.test.period)
            else:
                population = self.simulation.get_population(plural=key)
                if population is not None:  # If key is an entity plural
                    for instance_id, instance_values in expected_value.items():
                        for variable_name, value in instance_values.items():
                            entity_index = population.get_index(instance_id)
                            self.check_variable(
                                variable_name,
                                value,
                                self.test.period,
                                entity_index,
                            )
                else:
                    raise VariableNotFound(key, self.tax_benefit_system)

    def check_variable(
        self,
        variable_name: str,
        expected_value,
        period,
        entity_index=None,
    ):
        if self.should_ignore_variable(variable_name):
            return None

        if isinstance(expected_value, dict):
            for requested_period, expected_value_at_period in expected_value.items():
                self.check_variable(
                    variable_name,
                    expected_value_at_period,
                    requested_period,
                    entity_index,
                )

            return None

        actual_value = self.simulation.calculate(variable_name, period)

        if entity_index is not None:
            actual_value = actual_value[entity_index]

        return assert_near(
            actual_value,
            expected_value,
            self.test.absolute_error_margin[variable_name],
            f"{variable_name}@{period}: ",
            self.test.relative_error_margin[variable_name],
        )

    def should_ignore_variable(self, variable_name: str):
        only_variables = self.options.get("only_variables")
        ignore_variables = self.options.get("ignore_variables")
        variable_ignored = (
            ignore_variables is not None and variable_name in ignore_variables
        )
        variable_not_tested = (
            only_variables is not None and variable_name not in only_variables
        )

        return variable_ignored or variable_not_tested

    def repr_failure(self, excinfo):
        if not isinstance(
            excinfo.value,
            (AssertionError, VariableNotFound, SituationParsingError),
        ):
            return super().repr_failure(excinfo)

        message = excinfo.value.args[0]
        if isinstance(excinfo.value, SituationParsingError):
            message = f"Could not parse situation described: {message}"

        return os.linesep.join(
            [
                f"{self.path!s}:",
                f"  Test '{self.name!s}':",
                textwrap.indent(message, "    "),
            ],
        )


class OpenFiscaPlugin:
    def __init__(self, tax_benefit_system, options) -> None:
        self.tax_benefit_system = tax_benefit_system
        self.options = options

    def pytest_collect_file(self, parent, path):
        """Called by pytest for all plugins.
        :return: The collector for test methods.
        """
        if path.ext in [".yaml", ".yml"]:
            return YamlFile.from_parent(
                parent,
                path=pathlib.Path(path),
                tax_benefit_system=self.tax_benefit_system,
                options=self.options,
            )
        return None


def _get_tax_benefit_system(baseline, reforms, extensions):
    if not isinstance(reforms, list):
        reforms = [reforms]
    if not isinstance(extensions, list):
        extensions = [extensions]

    # keep reforms order in cache, ignore extensions order
    key = hash((id(baseline), ":".join(reforms), frozenset(extensions)))
    if _tax_benefit_system_cache.get(key):
        return _tax_benefit_system_cache.get(key)

    current_tax_benefit_system = baseline.clone()

    for reform_path in reforms:
        current_tax_benefit_system = current_tax_benefit_system.apply_reform(
            reform_path,
        )

    for extension in extensions:
        current_tax_benefit_system.load_extension(extension)

    _tax_benefit_system_cache[key] = current_tax_benefit_system

    return current_tax_benefit_system
