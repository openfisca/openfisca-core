# -*- coding: utf-8 -*-

import json
import os
import csv
import numpy
from pytest import fixture, mark, raises, approx

from openfisca_core.simulations import Simulation, CycleError, SpiralError
from openfisca_core.tracers import (
    SimpleTracer,
    FullTracer,
    TracingParameterNodeAtInstant,
    TraceNode,
)
from openfisca_country_template.variables.housing import HousingOccupancyStatus
from .parameters_fancy_indexing.test_fancy_indexing import parameters


class StubSimulation(Simulation):
    def __init__(self):
        self.exception = None
        self.max_spiral_loops = 1

    def _calculate(self, variable, period):
        if self.exception:
            raise self.exception

    def invalidate_cache_entry(self, variable, period):
        pass

    def purge_cache_of_invalid_values(self):
        pass


class MockTracer:
    def record_calculation_start(self, variable, period):
        self.calculation_start_recorded = True

    def record_calculation_result(self, value):
        self.recorded_result = True

    def record_calculation_end(self):
        self.calculation_end_recorded = True


@fixture
def tracer():
    return FullTracer()


@mark.parametrize("tracer", [SimpleTracer(), FullTracer()])
def test_stack_one_level(tracer):
    tracer.record_calculation_start("a", 2017)
    assert len(tracer.stack) == 1
    assert tracer.stack == [{"name": "a", "period": 2017}]

    tracer.record_calculation_end()
    assert tracer.stack == []


@mark.parametrize("tracer", [SimpleTracer(), FullTracer()])
def test_stack_two_levels(tracer):
    tracer.record_calculation_start("a", 2017)
    tracer.record_calculation_start("b", 2017)
    assert len(tracer.stack) == 2
    assert tracer.stack == [
        {"name": "a", "period": 2017},
        {"name": "b", "period": 2017},
    ]

    tracer.record_calculation_end()
    assert len(tracer.stack) == 1
    assert tracer.stack == [{"name": "a", "period": 2017}]


@mark.parametrize("tracer", [SimpleTracer(), FullTracer()])
def test_tracer_contract(tracer):
    simulation = StubSimulation()
    simulation.tracer = MockTracer()

    simulation.calculate("a", 2017)

    assert simulation.tracer.calculation_start_recorded
    assert simulation.tracer.calculation_end_recorded


def test_exception_robustness():
    simulation = StubSimulation()
    simulation.tracer = MockTracer()
    simulation.exception = Exception(":-o")

    with raises(Exception):
        simulation.calculate("a", 2017)

    assert simulation.tracer.calculation_start_recorded
    assert simulation.tracer.calculation_end_recorded


@mark.parametrize("tracer", [SimpleTracer(), FullTracer()])
def test_cycle_error(tracer):
    simulation = StubSimulation()
    simulation.tracer = tracer
    tracer.record_calculation_start("a", 2017)
    simulation._check_for_cycle("a", 2017)

    tracer.record_calculation_start("a", 2017)
    with raises(CycleError):
        simulation._check_for_cycle("a", 2017)


@mark.parametrize("tracer", [SimpleTracer(), FullTracer()])
def test_spiral_error(tracer):
    simulation = StubSimulation()
    simulation.tracer = tracer
    tracer.record_calculation_start("a", 2017)
    tracer.record_calculation_start("a", 2016)
    tracer.record_calculation_start("a", 2015)

    with raises(SpiralError):
        simulation._check_for_cycle("a", 2015)


def test_full_tracer_one_calculation(tracer):
    tracer._enter_calculation("a", 2017)
    tracer._exit_calculation()
    assert tracer.stack == []
    assert len(tracer.trees) == 1
    assert tracer.trees[0].name == "a"
    assert tracer.trees[0].period == 2017
    assert tracer.trees[0].children == []


def test_full_tracer_2_branches(tracer):
    tracer._enter_calculation("a", 2017)

    tracer._enter_calculation("b", 2017)
    tracer._exit_calculation()

    tracer._enter_calculation("c", 2017)
    tracer._exit_calculation()

    tracer._exit_calculation()

    assert len(tracer.trees) == 1
    assert len(tracer.trees[0].children) == 2


def test_full_tracer_2_trees(tracer):
    tracer._enter_calculation("b", 2017)
    tracer._exit_calculation()

    tracer._enter_calculation("c", 2017)
    tracer._exit_calculation()

    assert len(tracer.trees) == 2


def test_full_tracer_3_generations(tracer):
    tracer._enter_calculation("a", 2017)
    tracer._enter_calculation("b", 2017)
    tracer._enter_calculation("c", 2017)
    tracer._exit_calculation()
    tracer._exit_calculation()
    tracer._exit_calculation()

    assert len(tracer.trees) == 1
    assert len(tracer.trees[0].children) == 1
    assert len(tracer.trees[0].children[0].children) == 1


def test_full_tracer_variable_nb_requests(tracer):
    tracer._enter_calculation("a", "2017-01")
    tracer._enter_calculation("a", "2017-02")

    assert tracer.get_nb_requests("a") == 2


def test_simulation_calls_record_calculation_result():
    simulation = StubSimulation()
    simulation.tracer = MockTracer()

    simulation.calculate("a", 2017)

    assert simulation.tracer.recorded_result


def test_record_calculation_result(tracer):
    tracer._enter_calculation("a", 2017)
    tracer.record_calculation_result(numpy.asarray(100))
    tracer._exit_calculation()

    assert tracer.trees[0].value == 100


def test_flat_trace(tracer):
    tracer._enter_calculation("a", 2019)
    tracer._enter_calculation("b", 2019)
    tracer._exit_calculation()
    tracer._exit_calculation()

    trace = tracer.get_flat_trace()

    assert len(trace) == 2
    assert trace["a<2019>"]["dependencies"] == ["b<2019>"]
    assert trace["b<2019>"]["dependencies"] == []


def test_flat_trace_serialize_vectorial_values(tracer):
    tracer._enter_calculation("a", 2019)
    tracer.record_parameter_access("x.y.z", 2019, numpy.asarray([100, 200, 300]))
    tracer.record_calculation_result(numpy.asarray([10, 20, 30]))
    tracer._exit_calculation()

    trace = tracer.get_serialized_flat_trace()

    assert json.dumps(trace["a<2019>"]["value"])
    assert json.dumps(trace["a<2019>"]["parameters"]["x.y.z<2019>"])


def test_flat_trace_with_parameter(tracer):
    tracer._enter_calculation("a", 2019)
    tracer.record_parameter_access("p", "2019-01-01", 100)
    tracer._exit_calculation()

    trace = tracer.get_flat_trace()

    assert len(trace) == 1
    assert trace["a<2019>"]["parameters"] == {"p<2019-01-01>": 100}


def test_flat_trace_with_cache(tracer):
    tracer._enter_calculation("a", 2019)
    tracer._enter_calculation("b", 2019)
    tracer._enter_calculation("c", 2019)
    tracer._exit_calculation()
    tracer._exit_calculation()
    tracer._exit_calculation()
    tracer._enter_calculation("b", 2019)
    tracer._exit_calculation()

    trace = tracer.get_flat_trace()

    assert trace["b<2019>"]["dependencies"] == ["c<2019>"]


def test_calculation_time():
    tracer = FullTracer()

    tracer._enter_calculation("a", 2019)
    tracer._record_start_time(1500)
    tracer._record_end_time(2500)
    tracer._exit_calculation()

    performance_json = tracer.performance_log._json()
    assert performance_json["name"] == "All calculations"
    assert performance_json["value"] == 1000

    simulation_children = performance_json["children"]
    assert simulation_children[0]["name"] == "a<2019>"
    assert simulation_children[0]["value"] == 1000


@fixture
def tracer_calc_time():
    tracer = FullTracer()

    tracer._enter_calculation("a", 2019)
    tracer._record_start_time(1500)

    tracer._enter_calculation("b", 2019)
    tracer._record_start_time(1600)
    tracer._record_end_time(2300)
    tracer._exit_calculation()

    tracer._enter_calculation("c", 2019)
    tracer._record_start_time(2300)
    tracer._record_end_time(2400)
    tracer._exit_calculation()

    # Cache call
    tracer._enter_calculation("c", 2019)
    tracer._record_start_time(2400)
    tracer._record_end_time(2410)
    tracer._exit_calculation()

    tracer._record_end_time(2500)
    tracer._exit_calculation()

    tracer._enter_calculation("a", 2018)
    tracer._record_start_time(1800)
    tracer._record_end_time(1800 + 200)
    tracer._exit_calculation()

    return tracer


def test_calculation_time_with_depth(tracer_calc_time):
    tracer = tracer_calc_time
    performance_json = tracer.performance_log._json()
    simulation_grand_children = performance_json["children"][0]["children"]

    assert simulation_grand_children[0]["name"] == "b<2019>"
    assert simulation_grand_children[0]["value"] == 700


def test_flat_trace_calc_time(tracer_calc_time):
    tracer = tracer_calc_time
    flat_trace = tracer.get_flat_trace()

    assert flat_trace["a<2019>"]["calculation_time"] == 1000
    assert flat_trace["b<2019>"]["calculation_time"] == 700
    assert flat_trace["c<2019>"]["calculation_time"] == 100
    assert flat_trace["a<2019>"]["formula_time"] == 190  # 1000 - 700 - 100 - 10
    assert flat_trace["b<2019>"]["formula_time"] == 700
    assert flat_trace["c<2019>"]["formula_time"] == 100


def test_generate_performance_table(tracer_calc_time, tmpdir):
    tracer = tracer_calc_time
    tracer.generate_performance_tables(tmpdir)
    with open(os.path.join(tmpdir, "performance_table.csv"), "r") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        csv_rows = list(csv_reader)
    assert len(csv_rows) == 4
    a_row = next(row for row in csv_rows if row["name"] == "a<2019>")
    assert float(a_row["calculation_time"]) == 1000
    assert float(a_row["formula_time"]) == 190

    with open(
        os.path.join(tmpdir, "aggregated_performance_table.csv"), "r"
    ) as csv_file:
        aggregated_csv_reader = csv.DictReader(csv_file)
        aggregated_csv_rows = list(aggregated_csv_reader)
    assert len(aggregated_csv_rows) == 3
    a_row = next(row for row in aggregated_csv_rows if row["name"] == "a")
    assert float(a_row["calculation_time"]) == 1000 + 200
    assert float(a_row["formula_time"]) == 190 + 200


def test_get_aggregated_calculation_times(tracer_calc_time):
    perf_log = tracer_calc_time.performance_log
    aggregated_calculation_times = perf_log.aggregate_calculation_times(
        tracer_calc_time.get_flat_trace()
    )

    assert aggregated_calculation_times["a"]["calculation_time"] == 1000 + 200
    assert aggregated_calculation_times["a"]["formula_time"] == 190 + 200
    assert aggregated_calculation_times["a"]["avg_calculation_time"] == (1000 + 200) / 2
    assert aggregated_calculation_times["a"]["avg_formula_time"] == (190 + 200) / 2


def test_rounding():
    node_a = TraceNode("a", 2017)
    node_a.start = 1.23456789
    node_a.end = node_a.start + 1.23456789e-03

    assert node_a.calculation_time() == 1.235e-03  # Keep only 3 significant figures

    node_b = TraceNode("b", 2017)
    node_b.start = node_a.start
    node_b.end = node_a.end - 1.23456789e-08
    node_a.children = [node_b]

    assert (
        node_a.formula_time() == 1.235e-08
    )  # The rounding should not prevent from calculating a precise formula_time


def test_variable_stats(tracer):
    tracer._enter_calculation("A", 2017)
    tracer._enter_calculation("B", 2017)
    tracer._enter_calculation("B", 2017)
    tracer._enter_calculation("B", 2016)

    assert tracer.get_nb_requests("B") == 3
    assert tracer.get_nb_requests("A") == 1
    assert tracer.get_nb_requests("C") == 0


def test_log_format(tracer):
    tracer._enter_calculation("A", 2017)
    tracer._enter_calculation("B", 2017)
    tracer.record_calculation_result(numpy.asarray([1]))
    tracer._exit_calculation()
    tracer.record_calculation_result(numpy.asarray([2]))
    tracer._exit_calculation()

    lines = tracer.computation_log.lines()
    assert lines[0] == "  A<2017> >> [2]"
    assert lines[1] == "    B<2017> >> [1]"


def test_log_format_forest(tracer):
    tracer._enter_calculation("A", 2017)
    tracer.record_calculation_result(numpy.asarray([1]))
    tracer._exit_calculation()

    tracer._enter_calculation("B", 2017)
    tracer.record_calculation_result(numpy.asarray([2]))
    tracer._exit_calculation()

    lines = tracer.computation_log.lines()
    assert lines[0] == "  A<2017> >> [1]"
    assert lines[1] == "  B<2017> >> [2]"


def test_log_aggregate(tracer):
    tracer._enter_calculation("A", 2017)
    tracer.record_calculation_result(numpy.asarray([1]))
    tracer._exit_calculation()

    lines = tracer.computation_log.lines(aggregate=True)
    assert lines[0] == "  A<2017> >> {'avg': 1.0, 'max': 1, 'min': 1}"


def test_log_aggregate_with_enum(tracer):
    tracer._enter_calculation("A", 2017)
    tracer.record_calculation_result(
        HousingOccupancyStatus.encode(numpy.repeat("tenant", 100))
    )
    tracer._exit_calculation()

    lines = tracer.computation_log.lines(aggregate=True)
    assert (
        lines[0]
        == "  A<2017> >> {'avg': EnumArray(HousingOccupancyStatus.tenant), 'max': EnumArray(HousingOccupancyStatus.tenant), 'min': EnumArray(HousingOccupancyStatus.tenant)}"
    )


def test_log_aggregate_with_strings(tracer):
    tracer._enter_calculation("A", 2017)
    tracer.record_calculation_result(numpy.repeat("foo", 100))
    tracer._exit_calculation()

    lines = tracer.computation_log.lines(aggregate=True)
    assert lines[0] == "  A<2017> >> {'avg': '?', 'max': '?', 'min': '?'}"


def test_log_max_depth(tracer):
    tracer._enter_calculation("A", 2017)
    tracer._enter_calculation("B", 2017)
    tracer._enter_calculation("C", 2017)
    tracer.record_calculation_result(numpy.asarray([3]))
    tracer._exit_calculation()
    tracer.record_calculation_result(numpy.asarray([2]))
    tracer._exit_calculation()
    tracer.record_calculation_result(numpy.asarray([1]))
    tracer._exit_calculation()

    assert len(tracer.computation_log.lines()) == 3
    assert len(tracer.computation_log.lines(max_depth=4)) == 3
    assert len(tracer.computation_log.lines(max_depth=3)) == 3
    assert len(tracer.computation_log.lines(max_depth=2)) == 2
    assert len(tracer.computation_log.lines(max_depth=1)) == 1
    assert len(tracer.computation_log.lines(max_depth=0)) == 0


def test_no_wrapping(tracer):
    tracer._enter_calculation("A", 2017)
    tracer.record_calculation_result(
        HousingOccupancyStatus.encode(numpy.repeat("tenant", 100))
    )
    tracer._exit_calculation()

    lines = tracer.computation_log.lines()
    assert "'tenant'" in lines[0]
    assert "\n" not in lines[0]


def test_trace_enums(tracer):
    tracer._enter_calculation("A", 2017)
    tracer.record_calculation_result(
        HousingOccupancyStatus.encode(numpy.array(["tenant"]))
    )
    tracer._exit_calculation()

    lines = tracer.computation_log.lines()
    assert lines[0] == "  A<2017> >> ['tenant']"


#  Tests on tracing with fancy indexing
zone = numpy.asarray(["z1", "z2", "z2", "z1"])
housing_occupancy_status = numpy.asarray(["owner", "owner", "tenant", "tenant"])
family_status = numpy.asarray(["single", "couple", "single", "couple"])


def check_tracing_params(accessor, param_key):
    tracer = FullTracer()
    tracer._enter_calculation("A", "2015-01")
    tracingParams = TracingParameterNodeAtInstant(parameters("2015-01-01"), tracer)
    param = accessor(tracingParams)
    assert tracer.trees[0].parameters[0].name == param_key
    assert tracer.trees[0].parameters[0].value == approx(param)


@mark.parametrize(
    "test",
    [
        (lambda P: P.rate.single.owner.z1, "rate.single.owner.z1"),  # basic case
        (
            lambda P: P.rate.single.owner[zone],
            "rate.single.owner",
        ),  # fancy indexing on leaf
        (
            lambda P: P.rate.single[housing_occupancy_status].z1,
            "rate.single",
        ),  # on a node
        (
            lambda P: P.rate.single[housing_occupancy_status][zone],
            "rate.single",
        ),  # double fancy indexing
        (
            lambda P: P.rate[family_status][housing_occupancy_status].z2,
            "rate",
        ),  # double + node
        (
            lambda P: P.rate[family_status][housing_occupancy_status][zone],
            "rate",
        ),  # triple
    ],
)
def test_parameters(test):
    check_tracing_params(*test)


def test_browse_trace():
    tracer = FullTracer()

    tracer._enter_calculation("B", 2017)
    tracer._enter_calculation("C", 2017)
    tracer._exit_calculation()
    tracer._exit_calculation()
    tracer._enter_calculation("D", 2017)
    tracer._enter_calculation("E", 2017)
    tracer._exit_calculation()
    tracer._enter_calculation("F", 2017)
    tracer._exit_calculation()
    tracer._exit_calculation()

    browsed_nodes = [node.name for node in tracer.browse_trace()]
    assert browsed_nodes == ["B", "C", "D", "E", "F"]
