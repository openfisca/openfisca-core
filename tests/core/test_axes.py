import pytest

from openfisca_core.simulations import Axis, AxisArray, SimulationBuilder
from .test_simulation_builder import *  # noqa: F401


@pytest.fixture
def simulation_builder():
    return SimulationBuilder()


@pytest.fixture
def kwargs():
    return {
        "name": "salary",
        "count": 3,
        "min": 0,
        "max": 3000,
        }


@pytest.fixture
def axis(kwargs):
    return Axis(**kwargs)


@pytest.fixture
def axis_array():
    return AxisArray()


# Unit tests


def test_create_axis(kwargs):
    """
    Works! Missing fields are optional, so they default to None.
    """
    result = Axis(**kwargs)
    assert result.name == "salary"
    assert not result.period


def test_create_empty_axis():
    """
    Fails because we're not providing the required fields.
    """
    with pytest.raises(TypeError):
        Axis()


def test_empty_create_axis_array():
    """
    Nothing fancy, just an empty container.
    """
    result = AxisArray()
    assert isinstance(result, AxisArray)


def test_create_axis_array_with_axes(axis):
    """
    We can pass along some axes at initialisation time as well.
    """
    result = AxisArray(axes = [axis])
    assert result.first() == axis


def test_create_axis_array_with_anything(axis):
    """
    If you don't pass a collection, it will fail!
    """
    with pytest.raises(TypeError):
        AxisArray(axes = axis)


def test_create_axis_array_with_a_collection_of_anything():
    """
    If you pass a collection of anything, it will fail!
    """
    with pytest.raises(TypeError):
        AxisArray(axes = ["axis"])


def test_add_axis_to_array(axis_array, axis):
    """
    If you add an :obj:`Axis` to the array, it works!
    """
    result = axis_array.append(axis)
    assert axis in result


def test_add_anything_to_array(axis_array, axis):
    """
    If you add anything else to the array, it fails!
    """
    with pytest.raises(TypeError):
        axis_array.append("cuack")

# With periods


def test_add_axis_without_period(simulation_builder, persons):
    simulation_builder.set_default_period('2018-11')
    simulation_builder.add_person_entity(persons, {'Alicia': {}})
    simulation_builder.register_variable('salary', persons)
    simulation_builder.add_parallel_axis({'count': 3, 'name': 'salary', 'min': 0, 'max': 3000})
    simulation_builder.expand_axes()
    assert simulation_builder.get_input('salary', '2018-11') == pytest.approx([0, 1500, 3000])


# With variables


def test_add_axis_on_a_non_existing_variable(simulation_builder, persons):
    simulation_builder.add_person_entity(persons, {'Alicia': {}})
    simulation_builder.add_parallel_axis({'count': 3, 'name': 'ubi', 'min': 0, 'max': 3000, 'period': '2018-11'})

    with pytest.raises(KeyError):
        simulation_builder.expand_axes()


def test_add_axis_on_an_existing_variable_with_input(simulation_builder, persons):
    simulation_builder.add_person_entity(persons, {'Alicia': {'salary': {'2018-11': 1000}}})
    simulation_builder.register_variable('salary', persons)
    simulation_builder.add_parallel_axis({'count': 3, 'name': 'salary', 'min': 0, 'max': 3000, 'period': '2018-11'})
    simulation_builder.expand_axes()
    assert simulation_builder.get_input('salary', '2018-11') == pytest.approx([0, 1500, 3000])
    assert simulation_builder.get_count('persons') == 3
    assert simulation_builder.get_ids('persons') == ['Alicia0', 'Alicia1', 'Alicia2']


# With entities


def test_add_axis_on_persons(simulation_builder, persons):
    simulation_builder.add_person_entity(persons, {'Alicia': {}})
    simulation_builder.register_variable('salary', persons)
    simulation_builder.add_parallel_axis({'count': 3, 'name': 'salary', 'min': 0, 'max': 3000, 'period': '2018-11'})
    simulation_builder.expand_axes()
    assert simulation_builder.get_input('salary', '2018-11') == pytest.approx([0, 1500, 3000])
    assert simulation_builder.get_count('persons') == 3
    assert simulation_builder.get_ids('persons') == ['Alicia0', 'Alicia1', 'Alicia2']


def test_add_two_axes(simulation_builder, persons):
    simulation_builder.add_person_entity(persons, {'Alicia': {}})
    simulation_builder.register_variable('salary', persons)
    simulation_builder.add_parallel_axis({'count': 3, 'name': 'salary', 'min': 0, 'max': 3000, 'period': '2018-11'})
    simulation_builder.add_parallel_axis({'count': 3, 'name': 'pension', 'min': 0, 'max': 2000, 'period': '2018-11'})
    simulation_builder.expand_axes()
    assert simulation_builder.get_input('salary', '2018-11') == pytest.approx([0, 1500, 3000])
    assert simulation_builder.get_input('pension', '2018-11') == pytest.approx([0, 1000, 2000])


def test_add_axis_with_group(simulation_builder, persons):
    simulation_builder.add_person_entity(persons, {'Alicia': {}, 'Javier': {}})
    simulation_builder.register_variable('salary', persons)
    simulation_builder.add_parallel_axis({'count': 2, 'name': 'salary', 'min': 0, 'max': 3000, 'period': '2018-11'})
    simulation_builder.add_parallel_axis({'count': 2, 'name': 'salary', 'min': 0, 'max': 3000, 'period': '2018-11', 'index': 1})
    simulation_builder.expand_axes()
    assert simulation_builder.get_count('persons') == 4
    assert simulation_builder.get_ids('persons') == ['Alicia0', 'Javier1', 'Alicia2', 'Javier3']
    assert simulation_builder.get_input('salary', '2018-11') == pytest.approx([0, 0, 3000, 3000])


def test_add_axis_with_group_int_period(simulation_builder, persons):
    simulation_builder.add_person_entity(persons, {'Alicia': {}, 'Javier': {}})
    simulation_builder.register_variable('salary', persons)
    simulation_builder.add_parallel_axis({'count': 2, 'name': 'salary', 'min': 0, 'max': 3000, 'period': 2018})
    simulation_builder.add_parallel_axis({'count': 2, 'name': 'salary', 'min': 0, 'max': 3000, 'period': 2018, 'index': 1})
    simulation_builder.expand_axes()
    assert simulation_builder.get_input('salary', '2018') == pytest.approx([0, 0, 3000, 3000])


def test_add_axis_on_group_entity(simulation_builder, persons, group_entity):
    simulation_builder.add_person_entity(persons, {'Alicia': {}, 'Javier': {}, 'Tom': {}})
    simulation_builder.add_group_entity('persons', ['Alicia', 'Javier', 'Tom'], group_entity, {
        'housea': {'parents': ['Alicia', 'Javier']},
        'houseb': {'parents': ['Tom']},
        })
    simulation_builder.register_variable('rent', group_entity)
    simulation_builder.add_parallel_axis({'count': 2, 'name': 'rent', 'min': 0, 'max': 3000, 'period': '2018-11'})
    simulation_builder.expand_axes()
    assert simulation_builder.get_count('households') == 4
    assert simulation_builder.get_ids('households') == ['housea0', 'houseb1', 'housea2', 'houseb3']
    assert simulation_builder.get_input('rent', '2018-11') == approx([0, 0, 3000, 0])


def test_axis_on_group_expands_persons(simulation_builder, persons, group_entity):
    simulation_builder.add_person_entity(persons, {'Alicia': {}, 'Javier': {}, 'Tom': {}})
    simulation_builder.add_group_entity('persons', ['Alicia', 'Javier', 'Tom'], group_entity, {
        'housea': {'parents': ['Alicia', 'Javier']},
        'houseb': {'parents': ['Tom']},
        })
    simulation_builder.register_variable('rent', group_entity)
    simulation_builder.add_parallel_axis({'count': 2, 'name': 'rent', 'min': 0, 'max': 3000, 'period': '2018-11'})
    simulation_builder.expand_axes()
    assert simulation_builder.get_count('persons') == 6


def test_add_axis_distributes_roles(simulation_builder, persons, group_entity):
    simulation_builder.add_person_entity(persons, {'Alicia': {}, 'Javier': {}, 'Tom': {}})
    simulation_builder.add_group_entity('persons', ['Alicia', 'Javier', 'Tom'], group_entity, {
        'housea': {'parents': ['Alicia']},
        'houseb': {'parents': ['Tom'], 'children': ['Javier']},
        })
    simulation_builder.register_variable('rent', group_entity)
    simulation_builder.add_parallel_axis({'count': 2, 'name': 'rent', 'min': 0, 'max': 3000, 'period': '2018-11'})
    simulation_builder.expand_axes()
    assert [role.key for role in simulation_builder.get_roles('households')] == ['parent', 'child', 'parent', 'parent', 'child', 'parent']


def test_add_axis_on_persons_distributes_roles(simulation_builder, persons, group_entity):
    simulation_builder.add_person_entity(persons, {'Alicia': {}, 'Javier': {}, 'Tom': {}})
    simulation_builder.add_group_entity('persons', ['Alicia', 'Javier', 'Tom'], group_entity, {
        'housea': {'parents': ['Alicia']},
        'houseb': {'parents': ['Tom'], 'children': ['Javier']},
        })
    simulation_builder.register_variable('salary', persons)
    simulation_builder.add_parallel_axis({'count': 2, 'name': 'salary', 'min': 0, 'max': 3000, 'period': '2018-11'})
    simulation_builder.expand_axes()
    assert [role.key for role in simulation_builder.get_roles('households')] == ['parent', 'child', 'parent', 'parent', 'child', 'parent']


def test_add_axis_distributes_memberships(simulation_builder, persons, group_entity):
    simulation_builder.add_person_entity(persons, {'Alicia': {}, 'Javier': {}, 'Tom': {}})
    simulation_builder.add_group_entity('persons', ['Alicia', 'Javier', 'Tom'], group_entity, {
        'housea': {'parents': ['Alicia']},
        'houseb': {'parents': ['Tom'], 'children': ['Javier']},
        })
    simulation_builder.register_variable('rent', group_entity)
    simulation_builder.add_parallel_axis({'count': 2, 'name': 'rent', 'min': 0, 'max': 3000, 'period': '2018-11'})
    simulation_builder.expand_axes()
    assert simulation_builder.get_memberships('households') == [0, 1, 1, 2, 3, 3]


def test_add_perpendicular_axes(simulation_builder, persons):
    simulation_builder.add_person_entity(persons, {'Alicia': {}})
    simulation_builder.register_variable('salary', persons)
    simulation_builder.register_variable('pension', persons)
    simulation_builder.add_parallel_axis({'count': 3, 'name': 'salary', 'min': 0, 'max': 3000, 'period': '2018-11'})
    simulation_builder.add_perpendicular_axis({'count': 2, 'name': 'pension', 'min': 0, 'max': 2000, 'period': '2018-11'})
    simulation_builder.expand_axes()
    assert simulation_builder.get_input('salary', '2018-11') == pytest.approx([0, 1500, 3000, 0, 1500, 3000])
    assert simulation_builder.get_input('pension', '2018-11') == pytest.approx([0, 0, 0, 2000, 2000, 2000])


def test_add_perpendicular_axis_on_an_existing_variable_with_input(simulation_builder, persons):
    simulation_builder.add_person_entity(persons, {
        'Alicia': {
            'salary': {'2018-11': 1000},
            'pension': {'2018-11': 1000},
            },
        },)
    simulation_builder.register_variable('salary', persons)
    simulation_builder.register_variable('pension', persons)
    simulation_builder.add_parallel_axis({'count': 3, 'name': 'salary', 'min': 0, 'max': 3000, 'period': '2018-11'})
    simulation_builder.add_perpendicular_axis({'count': 2, 'name': 'pension', 'min': 0, 'max': 2000, 'period': '2018-11'})
    simulation_builder.expand_axes()
    assert simulation_builder.get_input('salary', '2018-11') == pytest.approx([0, 1500, 3000, 0, 1500, 3000])
    assert simulation_builder.get_input('pension', '2018-11') == pytest.approx([0, 0, 0, 2000, 2000, 2000])

# Integration test


def test_simulation_with_axes(simulation_builder):
    from .test_countries import tax_benefit_system
    input_yaml = """
        persons:
          Alicia: {salary: {2018-11: 0}}
          Javier: {}
          Tom: {}
        households:
          housea:
            parents: [Alicia, Javier]
          houseb:
            parents: [Tom]
        axes:
            -
                - count: 2
                  name: rent
                  min: 0
                  max: 3000
                  period: 2018-11
    """
    data = yaml.safe_load(input_yaml)
    simulation = simulation_builder.build_from_dict(tax_benefit_system, data)
    assert simulation.get_array('salary', '2018-11') == pytest.approx([0, 0, 0, 0, 0, 0])
    assert simulation.get_array('rent', '2018-11') == pytest.approx([0, 0, 3000, 0])
