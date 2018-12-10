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
    assert simulation_builder.get_count('persons') == 3
    assert simulation_builder.get_ids('persons') == ['Alicia0', 'Alicia1', 'Alicia2']


def test_add_two_axes(simulation_builder, persons):
    simulation_builder.add_person_entity(persons, {'Alicia': {}})
    simulation_builder.add_parallel_axis({'count': 3, 'name': 'salary', 'min': 0, 'max': 3000, 'period': '2018-11'})
    simulation_builder.add_parallel_axis({'count': 3, 'name': 'pension', 'min': 0, 'max': 2000, 'period': '2018-11'})
    simulation_builder.expand_axes()
    assert simulation_builder.get_input('salary', '2018-11') == approx([0, 1500, 3000])
    assert simulation_builder.get_input('pension', '2018-11') == approx([0, 1000, 2000])


def test_add_axis_with_group(simulation_builder, persons):
    simulation_builder.add_person_entity(persons, {'Alicia': {}, 'Javier': {}})
    simulation_builder.add_parallel_axis({'count': 2, 'name': 'salary', 'min': 0, 'max': 3000, 'period': '2018-11'})
    simulation_builder.expand_axes()
    assert simulation_builder.get_count('persons') == 4
    assert simulation_builder.get_ids('persons') == ['Alicia0', 'Javier1', 'Alicia2', 'Javier3']
