# -*- coding: utf-8 -*-

from pytest import raises, mark
import numpy as np

from openfisca_core.simulations import Simulation
from openfisca_core.tracers import SimpleTracer, FullTracer
from openfisca_core.simulations import CycleError, SpiralError


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

    def record_calculation_result(self, value):
        self.recorded_result = True

    def exit_calculation(self):
        self.exited = True


@mark.parametrize("tracer", [SimpleTracer(), FullTracer()])
def test_stack_one_level(tracer):
    tracer.enter_calculation('toto', 2017)
    assert len(tracer.stack) == 1
    assert tracer.stack[0]['name'] == 'toto'
    assert tracer.stack[0]['period'] == 2017

    tracer.exit_calculation()
    assert tracer.stack == []


@mark.parametrize("tracer", [SimpleTracer(), FullTracer()])
def test_stack_two_levels(tracer):
    tracer.enter_calculation('toto', 2017)
    tracer.enter_calculation('tata', 2017)
    assert len(tracer.stack) == 2
    assert tracer.stack[0]['name'] == 'toto'
    assert tracer.stack[0]['period'] == 2017
    assert tracer.stack[1]['name'] == 'tata'
    assert tracer.stack[1]['period'] == 2017

    tracer.exit_calculation()
    assert len(tracer.stack) == 1
    assert tracer.stack[0]['name'] == 'toto'
    assert tracer.stack[0]['period'] == 2017


@mark.parametrize("tracer", [SimpleTracer(), FullTracer()])
def test_tracer_contract(tracer):
    simulation = StubSimulation()
    simulation.tracer = MockTracer()

    simulation.calculate('toto', 2017)

    assert simulation.tracer.entered
    assert simulation.tracer.exited


def test_exception_robustness():
    simulation = StubSimulation()
    simulation.tracer = MockTracer()
    simulation.exception = Exception(":-o")

    with raises(Exception):
        simulation.calculate('toto', 2017)

    assert simulation.tracer.entered
    assert simulation.tracer.exited


@mark.parametrize("tracer", [SimpleTracer(), FullTracer()])
def test_cycle_error(tracer):
    simulation = StubSimulation()
    simulation.tracer = tracer
    tracer.enter_calculation('toto', 2017)
    simulation._check_for_cycle('toto', 2017)

    tracer.enter_calculation('toto', 2017)
    with raises(CycleError):
        simulation._check_for_cycle('toto', 2017)


@mark.parametrize("tracer", [SimpleTracer(), FullTracer()])
def test_spiral_error(tracer):
    simulation = StubSimulation()
    simulation.tracer = tracer
    tracer.enter_calculation('toto', 2017)
    tracer.enter_calculation('toto', 2016)
    tracer.enter_calculation('toto', 2015)

    with raises(SpiralError):
        simulation._check_for_cycle('toto', 2015)


def test_full_tracer_one_calculation():
    tracer = FullTracer()
    tracer.enter_calculation('toto', 2017)
    tracer.exit_calculation()
    assert tracer.stack == []
    assert len(tracer.trees) == 1
    assert tracer.trees[0]['name'] == 'toto'
    assert tracer.trees[0]['period'] == 2017
    assert tracer.trees[0]['children'] == []


def test_full_tracer_2_branches():
    tracer = FullTracer()
    tracer.enter_calculation('toto', 2017)

    tracer.enter_calculation('tata', 2017)
    tracer.exit_calculation()

    tracer.enter_calculation('titi', 2017)
    tracer.exit_calculation()

    tracer.exit_calculation()

    assert len(tracer.trees) == 1
    assert len(tracer.trees[0]['children']) == 2


def test_full_tracer_2_trees():
    tracer = FullTracer()
    tracer.enter_calculation('tata', 2017)
    tracer.exit_calculation()

    tracer.enter_calculation('titi', 2017)
    tracer.exit_calculation()

    assert len(tracer.trees) == 2


def test_full_tracer_3_generations():
    tracer = FullTracer()
    tracer.enter_calculation('toto', 2017)
    tracer.enter_calculation('tata', 2017)
    tracer.enter_calculation('titi', 2017)
    tracer.exit_calculation()
    tracer.exit_calculation()
    tracer.exit_calculation()

    assert len(tracer.trees) == 1
    assert len(tracer.trees[0]['children']) == 1
    assert len(tracer.trees[0]['children'][0]['children']) == 1


def test_full_tracer_variable_nb_requests():
    tracer = FullTracer()
    tracer.enter_calculation('toto', '2017-01')
    tracer.enter_calculation('toto', '2017-02')

    assert tracer.get_nb_requests('toto') == 2


def test_simulation_calls_record_calculation_result():
    simulation = StubSimulation()
    simulation.tracer = MockTracer()

    simulation.calculate('toto', 2017)

    assert simulation.tracer.recorded_result


def test_record_calculation_result():
    tracer = FullTracer()
    tracer.enter_calculation('toto', 2017)
    tracer.record_calculation_result(np.asarray(100))
    tracer.exit_calculation()

    assert tracer.trees[0]['value'] == 100


def test_flat_trace():
    tracer = FullTracer()
    tracer.enter_calculation('a', 2019)
    tracer.enter_calculation('b', 2019)
    tracer.exit_calculation()
    tracer.exit_calculation()

    trace = tracer.get_flat_trace()

    assert len(trace) == 2
    assert trace['a<2019>']['dependencies'] == ['b<2019>']
    assert trace['b<2019>']['dependencies'] == []


def test_flat_trace_with_cache():
    tracer = FullTracer()
    tracer.enter_calculation('a', 2019)
    tracer.enter_calculation('b', 2019)
    tracer.enter_calculation('c', 2019)
    tracer.exit_calculation()
    tracer.exit_calculation()
    tracer.enter_calculation('b', 2019)
    tracer.exit_calculation()
    tracer.exit_calculation()

    trace = tracer.get_flat_trace()

    assert trace['b<2019>']['dependencies'] == ['c<2019>']


def test_flat_trace_with_parameter():
    tracer = FullTracer()
    tracer.enter_calculation('a', 2019)
    tracer.record_parameter_access('p', '2019-01-01', 100)
    tracer.exit_calculation()

    trace = tracer.get_flat_trace()

    assert len(trace) == 1
    assert trace['a<2019>']['parameters'] == {'p<2019-01-01>': 100}
