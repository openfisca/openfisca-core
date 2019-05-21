# -*- coding: utf-8 -*-

from openfisca_core.unified_tracing import SimpleTracer
from pytest import fixture


class DummySimulation:

    def __init__(self):
        self.tracer = SimpleTracer()

    def calculate(self, variable, period, **parameters):
        self.tracer.record(variable.__class__.__name__, period)
        variable.formula(self, period)

class v0:

    def __init__(self, simulation):
        self.simulation = DummySimulation()

    def formula(self, simulation, period):
        simulation.calculate(v1(), period)
        simulation.calculate(v2(), period)


class v1:

    def formula(self, simulation, period):
        pass


class v2:

    def formula(self, simulation, period):
        pass


@fixture
def simulation():
    return DummySimulation()


def test_record(simulation):
    variable = v0(simulation)
    period = '2019-01'

    simulation.calculate(variable, period)

    stack = simulation.tracer.stack
    assert stack == {
        'name': 'v0',
        'period': '2019-01',  
        'children': [
            {
                'name': 'v1',
                'period': '2019-01'
            },
            {
                'name': 'v2',
                'period': '2019-01'
            }
        ]
    }, stack
