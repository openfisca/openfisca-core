# -*- coding: utf-8 -*-

from pytest import raises

from openfisca_core.simulations import Simulation
from openfisca_core.tracers import SimpleTracer
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


class MockTracer(SimpleTracer):

    def enter_calculation(self, variable, period):
        self.entered = True

    def exit_calculation(self):
        self.exited = True


def test_stack_one_level():
    tracer = SimpleTracer()

    tracer.enter_calculation('toto', 2017)
    assert len(tracer.stack) == 1
    assert tracer.stack == [{'name': 'toto', 'period': 2017}]

    tracer.exit_calculation()
    assert tracer.stack == []


def test_stack_two_levels():
    tracer = SimpleTracer()

    tracer.enter_calculation('toto', 2017)
    tracer.enter_calculation('tata', 2017)
    assert len(tracer.stack) == 2
    assert tracer.stack == [{'name': 'toto', 'period': 2017}, {'name': 'tata', 'period': 2017}]

    tracer.exit_calculation()
    assert tracer.stack == [{'name': 'toto', 'period': 2017}]


def test_tracer_contract():
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


def test_cycle_error():
    simulation = StubSimulation()
    tracer = SimpleTracer()
    simulation.tracer = tracer
    tracer.enter_calculation('toto', 2017)
    simulation._check_for_cycle('toto', 2017)

    tracer.enter_calculation('toto', 2017)
    with raises(CycleError):
        simulation._check_for_cycle('toto', 2017)

def test_spiral_error():
    simulation = StubSimulation()
    tracer = SimpleTracer()
    simulation.tracer = tracer
    tracer.enter_calculation('toto', 2017)
    tracer.enter_calculation('toto', 2016)
    tracer.enter_calculation('toto', 2015)

    with raises(SpiralError):
        simulation._check_for_cycle('toto', 2015)
