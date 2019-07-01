# -*- coding: utf-8 -*-

import json
import numpy as np
from pytest import fixture, mark, raises, approx

from openfisca_core.simulations import Simulation, CycleError, SpiralError
from openfisca_core.tracers import SimpleTracer, FullTracer, TracingParameterNodeAtInstant
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

    def enter_calculation(self, variable, period):
        self.entered = True

    def record_start(self, timestamp):
        self.timer_started = True

    def record_calculation_result(self, value):
        self.recorded_result = True

    def record_end(self, timestamp):
        self.timer_ended = True

    def exit_calculation(self):
        self.exited = True


@fixture
def tracer():
    return FullTracer()


@mark.parametrize("tracer", [SimpleTracer(), FullTracer()])
def test_stack_one_level(tracer):
    tracer.enter_calculation('a', 2017)
    assert len(tracer.stack) == 1
    assert tracer.stack == [{'name': 'a', 'period': 2017}]

    tracer.exit_calculation()
    assert tracer.stack == []


@mark.parametrize("tracer", [SimpleTracer(), FullTracer()])
def test_stack_two_levels(tracer):
    tracer.enter_calculation('a', 2017)
    tracer.enter_calculation('b', 2017)
    assert len(tracer.stack) == 2
    assert tracer.stack == [{'name': 'a', 'period': 2017}, {'name': 'b', 'period': 2017}]

    tracer.exit_calculation()
    assert len(tracer.stack) == 1
    assert tracer.stack == [{'name': 'a', 'period': 2017}]


@mark.parametrize("tracer", [SimpleTracer(), FullTracer()])
def test_tracer_contract(tracer):
    simulation = StubSimulation()
    simulation.tracer = MockTracer()

    simulation.calculate('a', 2017)

    assert simulation.tracer.entered
    assert simulation.tracer.timer_started
    assert simulation.tracer.timer_ended
    assert simulation.tracer.exited


def test_exception_robustness():
    simulation = StubSimulation()
    simulation.tracer = MockTracer()
    simulation.exception = Exception(":-o")

    with raises(Exception):
        simulation.calculate('a', 2017)

    assert simulation.tracer.entered
    assert simulation.tracer.exited


@mark.parametrize("tracer", [SimpleTracer(), FullTracer()])
def test_cycle_error(tracer):
    simulation = StubSimulation()
    simulation.tracer = tracer
    tracer.enter_calculation('a', 2017)
    simulation._check_for_cycle('a', 2017)

    tracer.enter_calculation('a', 2017)
    with raises(CycleError):
        simulation._check_for_cycle('a', 2017)


@mark.parametrize("tracer", [SimpleTracer(), FullTracer()])
def test_spiral_error(tracer):
    simulation = StubSimulation()
    simulation.tracer = tracer
    tracer.enter_calculation('a', 2017)
    tracer.enter_calculation('a', 2016)
    tracer.enter_calculation('a', 2015)

    with raises(SpiralError):
        simulation._check_for_cycle('a', 2015)


def test_full_tracer_one_calculation(tracer):
    tracer.enter_calculation('a', 2017)
    tracer.exit_calculation()
    assert tracer.stack == []
    assert len(tracer.trees) == 1
    assert tracer.trees[0]['name'] == 'a'
    assert tracer.trees[0]['period'] == 2017
    assert tracer.trees[0]['children'] == []


def test_full_tracer_2_branches(tracer):
    tracer.enter_calculation('a', 2017)

    tracer.enter_calculation('b', 2017)
    tracer.exit_calculation()

    tracer.enter_calculation('c', 2017)
    tracer.exit_calculation()

    tracer.exit_calculation()

    assert len(tracer.trees) == 1
    assert len(tracer.trees[0]['children']) == 2


def test_full_tracer_2_trees(tracer):
    tracer.enter_calculation('b', 2017)
    tracer.exit_calculation()

    tracer.enter_calculation('c', 2017)
    tracer.exit_calculation()

    assert len(tracer.trees) == 2


def test_full_tracer_3_generations(tracer):
    tracer.enter_calculation('a', 2017)
    tracer.enter_calculation('b', 2017)
    tracer.enter_calculation('c', 2017)
    tracer.exit_calculation()
    tracer.exit_calculation()
    tracer.exit_calculation()

    assert len(tracer.trees) == 1
    assert len(tracer.trees[0]['children']) == 1
    assert len(tracer.trees[0]['children'][0]['children']) == 1


def test_full_tracer_variable_nb_requests(tracer):
    tracer.enter_calculation('a', '2017-01')
    tracer.enter_calculation('a', '2017-02')

    assert tracer.get_nb_requests('a') == 2


def test_simulation_calls_record_calculation_result():
    simulation = StubSimulation()
    simulation.tracer = MockTracer()

    simulation.calculate('a', 2017)

    assert simulation.tracer.recorded_result


def test_record_calculation_result(tracer):
    tracer.enter_calculation('a', 2017)
    tracer.record_calculation_result(np.asarray(100))
    tracer.exit_calculation()

    assert tracer.trees[0]['value'] == 100


def test_flat_trace(tracer):
    tracer.enter_calculation('a', 2019)
    tracer.enter_calculation('b', 2019)
    tracer.exit_calculation()
    tracer.exit_calculation()

    trace = tracer.get_flat_trace()

    assert len(trace) == 2
    assert trace['a<2019>']['dependencies'] == ['b<2019>']
    assert trace['b<2019>']['dependencies'] == []


def test_flat_trace_serialize_vectorial_values(tracer):
    tracer.enter_calculation('a', 2019)
    tracer.record_parameter_access('x.y.z', 2019, np.asarray([100, 200, 300]))
    tracer.record_calculation_result(np.asarray([10, 20, 30]))
    tracer.exit_calculation()

    trace = tracer.get_flat_trace()

    assert json.dumps(trace['a<2019>']['value'])
    assert json.dumps(trace['a<2019>']['parameters']['x.y.z<2019>'])


def test_flat_trace_with_parameter(tracer):
    tracer.enter_calculation('a', 2019)
    tracer.record_parameter_access('p', '2019-01-01', 100)
    tracer.exit_calculation()

    trace = tracer.get_flat_trace()

    assert len(trace) == 1
    assert trace['a<2019>']['parameters'] == {'p<2019-01-01>': 100}


def test_flat_trace_with_cache(tracer):
    tracer.enter_calculation('a', 2019)
    tracer.enter_calculation('b', 2019)
    tracer.enter_calculation('c', 2019)
    tracer.exit_calculation()
    tracer.exit_calculation()
    tracer.exit_calculation()
    tracer.enter_calculation('b', 2019)
    tracer.exit_calculation()

    trace = tracer.get_flat_trace()

    assert trace['b<2019>']['dependencies'] == ['c<2019>']


def test_calculation_time():
    tracer = FullTracer()

    tracer.enter_calculation('a', 2019)
    tracer.record_start(1500)
    tracer.record_end(2500)
    tracer.exit_calculation()

    performance_json = tracer.performance_log.json()
    assert performance_json['name'] == 'simulation'
    assert performance_json['value'] == 1000

    simulation_children = performance_json['children']
    assert simulation_children[0]['name'] == 'a<2019>'
    assert simulation_children[0]['value'] == 1000


def test_variable_stats(tracer):
    tracer.enter_calculation("A", 2017)
    tracer.enter_calculation("B", 2017)
    tracer.enter_calculation("B", 2017)
    tracer.enter_calculation("B", 2016)

    assert tracer.get_nb_requests('B') == 3
    assert tracer.get_nb_requests('A') == 1
    assert tracer.get_nb_requests('C') == 0


def test_log_format(tracer):
    tracer.enter_calculation("A", 2017)
    tracer.enter_calculation("B", 2017)
    tracer.record_calculation_result(np.asarray([1]))
    tracer.exit_calculation()
    tracer.record_calculation_result(np.asarray([2]))
    tracer.exit_calculation()

    lines = tracer.computation_log.lines()
    assert lines[0] == '  A<2017> >> [2]'
    assert lines[1] == '    B<2017> >> [1]'


def test_log_format_forest(tracer):
    tracer.enter_calculation("A", 2017)
    tracer.record_calculation_result(np.asarray([1]))
    tracer.exit_calculation()

    tracer.enter_calculation("B", 2017)
    tracer.record_calculation_result(np.asarray([2]))
    tracer.exit_calculation()

    lines = tracer.computation_log.lines()
    assert lines[0] == '  A<2017> >> [1]'
    assert lines[1] == '  B<2017> >> [2]'


def test_log_aggregate(tracer):
    tracer.enter_calculation("A", 2017)
    tracer.record_calculation_result(np.asarray([1]))
    tracer.exit_calculation()

    lines = tracer.computation_log.lines(aggregate = True)
    assert lines[0] == "  A<2017> >> {'avg': 1.0, 'max': 1, 'min': 1}"


def test_log_aggregate_with_enum(tracer):
    tracer.enter_calculation("A", 2017)
    tracer.record_calculation_result(HousingOccupancyStatus.encode(np.repeat('tenant', 100)))
    tracer.exit_calculation()

    lines = tracer.computation_log.lines(aggregate = True)
    assert lines[0] == "  A<2017> >> {'avg': EnumArray(HousingOccupancyStatus.tenant), 'max': EnumArray(HousingOccupancyStatus.tenant), 'min': EnumArray(HousingOccupancyStatus.tenant)}"


def test_log_aggregate_with_strings(tracer):
    tracer.enter_calculation("A", 2017)
    tracer.record_calculation_result(np.repeat('foo', 100))
    tracer.exit_calculation()

    lines = tracer.computation_log.lines(aggregate = True)
    assert lines[0] == "  A<2017> >> {'avg': '?', 'max': '?', 'min': '?'}"


def test_no_wrapping(tracer):
    tracer.enter_calculation("A", 2017)
    tracer.record_calculation_result(HousingOccupancyStatus.encode(np.repeat('tenant', 100)))
    tracer.exit_calculation()

    lines = tracer.computation_log.lines()
    assert "'tenant'" in lines[0]
    assert "\n" not in lines[0]


def test_trace_enums(tracer):
    tracer.enter_calculation("A", 2017)
    tracer.record_calculation_result(HousingOccupancyStatus.encode(np.array(['tenant'])))
    tracer.exit_calculation()

    lines = tracer.computation_log.lines()
    assert lines[0] == "  A<2017> >> ['tenant']"


#  Tests on tracing with fancy indexing
zone = np.asarray(['z1', 'z2', 'z2', 'z1'])
housing_occupancy_status = np.asarray(['owner', 'owner', 'tenant', 'tenant'])
family_status = np.asarray(['single', 'couple', 'single', 'couple'])


def check_tracing_params(accessor, param_key):
    tracer = FullTracer()
    tracer.enter_calculation('A', '2015-01')
    tracingParams = TracingParameterNodeAtInstant(parameters('2015-01-01'), tracer)
    param = accessor(tracingParams)
    assert tracer.trees[0]['parameters'][0]['name'] == param_key
    assert tracer.trees[0]['parameters'][0]['value'] == approx(param)


@mark.parametrize("test", [
    (lambda P: P.rate.single.owner.z1, 'rate.single.owner.z1'),  # basic case
    (lambda P: P.rate.single.owner[zone], 'rate.single.owner'),  # fancy indexing on leaf
    (lambda P: P.rate.single[housing_occupancy_status].z1, 'rate.single'),  # on a node
    (lambda P: P.rate.single[housing_occupancy_status][zone], 'rate.single'),  # double fancy indexing
    (lambda P: P.rate[family_status][housing_occupancy_status].z2, 'rate'),  # double + node
    (lambda P: P.rate[family_status][housing_occupancy_status][zone], 'rate'),  # triple
    ])
def test_parameters(test):
    check_tracing_params(*test)
