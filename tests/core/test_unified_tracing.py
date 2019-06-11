# -*- coding: utf-8 -*-

from openfisca_core.simulations import Simulation
from openfisca_core.unified_tracing import SimpleTracer


class StubSimulation:
    
    def calculate(self, variable, period):
        self.tracer.enter_calculation(variable, period)
        self.tracer.exit_calculation()


class MockTracer:

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
