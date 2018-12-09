# -*- coding: utf-8 -*-
from pytest import fixture, approx

from openfisca_core.simulation_builder import SimulationBuilder
from .test_simulation_builder import *  # noqa: F401


@fixture
def simulation_builder():
    return SimulationBuilder()


def test_add_axis_on_persons(simulation_builder, persons):
    simulation_builder.add_person_entity(persons, {'Alicia': {}})
    simulation_builder.add_parallel_axis({'count': 3, 'name': 'salary', 'min': 0, 'max': 3000, 'period': '2018-11'})
    simulation_builder.expand_axes()
    assert simulation_builder.get_input('salary', '2018-11') == approx([0, 1500, 3000])
