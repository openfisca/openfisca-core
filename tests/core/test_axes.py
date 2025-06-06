import pytest

from openfisca_core import errors
from openfisca_core.simulations import SimulationBuilder
from openfisca_core.tools import test_runner

# With periods


def test_add_axis_without_period(persons) -> None:
    simulation_builder = SimulationBuilder()
    simulation_builder.set_default_period("2018-11")
    simulation_builder.add_person_entity(persons, {"Alicia": {}})
    simulation_builder.register_variable("salary", persons)
    simulation_builder.add_parallel_axis(
        {"count": 3, "name": "salary", "min": 0, "max": 3000},
    )
    simulation_builder.expand_axes()
    assert simulation_builder.get_input("salary", "2018-11") == pytest.approx(
        [0, 1500, 3000],
    )


# With variables


def test_add_axis_on_a_non_existing_variable(persons) -> None:
    simulation_builder = SimulationBuilder()
    simulation_builder.add_person_entity(persons, {"Alicia": {}})
    simulation_builder.add_parallel_axis(
        {"count": 3, "name": "ubi", "min": 0, "max": 3000, "period": "2018-11"},
    )

    with pytest.raises(KeyError):
        simulation_builder.expand_axes()


def test_add_axis_on_an_existing_variable_with_input(persons) -> None:
    simulation_builder = SimulationBuilder()
    simulation_builder.add_person_entity(
        persons,
        {"Alicia": {"salary": {"2018-11": 1000}}},
    )
    simulation_builder.register_variable("salary", persons)
    simulation_builder.add_parallel_axis(
        {"count": 3, "name": "salary", "min": 0, "max": 3000, "period": "2018-11"},
    )
    simulation_builder.expand_axes()
    assert simulation_builder.get_input("salary", "2018-11") == pytest.approx(
        [0, 1500, 3000],
    )
    assert simulation_builder.get_count("persons") == 3
    assert simulation_builder.get_ids("persons") == ["Alicia0", "Alicia1", "Alicia2"]


# With entities


def test_add_axis_on_persons(persons) -> None:
    simulation_builder = SimulationBuilder()
    simulation_builder.add_person_entity(persons, {"Alicia": {}})
    simulation_builder.register_variable("salary", persons)
    simulation_builder.add_parallel_axis(
        {"count": 3, "name": "salary", "min": 0, "max": 3000, "period": "2018-11"},
    )
    simulation_builder.expand_axes()
    assert simulation_builder.get_input("salary", "2018-11") == pytest.approx(
        [0, 1500, 3000],
    )
    assert simulation_builder.get_count("persons") == 3
    assert simulation_builder.get_ids("persons") == ["Alicia0", "Alicia1", "Alicia2"]


def test_add_two_axes(persons) -> None:
    simulation_builder = SimulationBuilder()
    simulation_builder.add_person_entity(persons, {"Alicia": {}})
    simulation_builder.register_variable("salary", persons)
    simulation_builder.add_parallel_axis(
        {"count": 3, "name": "salary", "min": 0, "max": 3000, "period": "2018-11"},
    )
    simulation_builder.add_parallel_axis(
        {"count": 3, "name": "pension", "min": 0, "max": 2000, "period": "2018-11"},
    )
    simulation_builder.expand_axes()
    assert simulation_builder.get_input("salary", "2018-11") == pytest.approx(
        [0, 1500, 3000],
    )
    assert simulation_builder.get_input("pension", "2018-11") == pytest.approx(
        [0, 1000, 2000],
    )


def test_add_axis_with_group(persons) -> None:
    simulation_builder = SimulationBuilder()
    simulation_builder.add_person_entity(persons, {"Alicia": {}, "Javier": {}})
    simulation_builder.register_variable("salary", persons)
    simulation_builder.add_parallel_axis(
        {"count": 2, "name": "salary", "min": 0, "max": 3000, "period": "2018-11"},
    )
    simulation_builder.add_parallel_axis(
        {
            "count": 2,
            "name": "salary",
            "min": 0,
            "max": 3000,
            "period": "2018-11",
            "index": 1,
        },
    )
    simulation_builder.expand_axes()
    assert simulation_builder.get_count("persons") == 4
    assert simulation_builder.get_ids("persons") == [
        "Alicia0",
        "Javier1",
        "Alicia2",
        "Javier3",
    ]
    assert simulation_builder.get_input("salary", "2018-11") == pytest.approx(
        [0, 0, 3000, 3000],
    )


def test_add_axis_with_group_int_period(persons) -> None:
    simulation_builder = SimulationBuilder()
    simulation_builder.add_person_entity(persons, {"Alicia": {}, "Javier": {}})
    simulation_builder.register_variable("salary", persons)
    simulation_builder.add_parallel_axis(
        {"count": 2, "name": "salary", "min": 0, "max": 3000, "period": 2018},
    )
    simulation_builder.add_parallel_axis(
        {
            "count": 2,
            "name": "salary",
            "min": 0,
            "max": 3000,
            "period": 2018,
            "index": 1,
        },
    )
    simulation_builder.expand_axes()
    assert simulation_builder.get_input("salary", "2018") == pytest.approx(
        [0, 0, 3000, 3000],
    )


def test_add_axis_on_households(persons, households) -> None:
    simulation_builder = SimulationBuilder()
    simulation_builder.add_person_entity(
        persons,
        {"Alicia": {}, "Javier": {}, "Tom": {}},
    )
    simulation_builder.add_group_entity(
        "persons",
        ["Alicia", "Javier", "Tom"],
        households,
        {
            "housea": {"adults": ["Alicia", "Javier"]},
            "houseb": {"adults": ["Tom"]},
        },
    )
    simulation_builder.register_variable("rent", households)
    simulation_builder.add_parallel_axis(
        {"count": 2, "name": "rent", "min": 0, "max": 3000, "period": "2018-11"},
    )
    simulation_builder.expand_axes()
    assert simulation_builder.get_count("households") == 4
    assert simulation_builder.get_ids("households") == [
        "housea0",
        "houseb1",
        "housea2",
        "houseb3",
    ]
    assert simulation_builder.get_input("rent", "2018-11") == pytest.approx(
        [0, 0, 3000, 0],
    )


def test_axis_on_group_expands_persons(persons, households) -> None:
    simulation_builder = SimulationBuilder()
    simulation_builder.add_person_entity(
        persons,
        {"Alicia": {}, "Javier": {}, "Tom": {}},
    )
    simulation_builder.add_group_entity(
        "persons",
        ["Alicia", "Javier", "Tom"],
        households,
        {
            "housea": {"adults": ["Alicia", "Javier"]},
            "houseb": {"adults": ["Tom"]},
        },
    )
    simulation_builder.register_variable("rent", households)
    simulation_builder.add_parallel_axis(
        {"count": 2, "name": "rent", "min": 0, "max": 3000, "period": "2018-11"},
    )
    simulation_builder.expand_axes()
    assert simulation_builder.get_count("persons") == 6


def test_add_axis_distributes_roles(persons, households) -> None:
    simulation_builder = SimulationBuilder()
    simulation_builder.add_person_entity(
        persons,
        {"Alicia": {}, "Javier": {}, "Tom": {}},
    )
    simulation_builder.add_group_entity(
        "persons",
        ["Alicia", "Javier", "Tom"],
        households,
        {
            "housea": {"adults": ["Alicia"]},
            "houseb": {"adults": ["Tom"], "children": ["Javier"]},
        },
    )
    simulation_builder.register_variable("rent", households)
    simulation_builder.add_parallel_axis(
        {"count": 2, "name": "rent", "min": 0, "max": 3000, "period": "2018-11"},
    )
    simulation_builder.expand_axes()
    assert [role.key for role in simulation_builder.get_roles("households")] == [
        "adult",
        "child",
        "adult",
        "adult",
        "child",
        "adult",
    ]


def test_add_axis_on_persons_distributes_roles(persons, households) -> None:
    simulation_builder = SimulationBuilder()
    simulation_builder.add_person_entity(
        persons,
        {"Alicia": {}, "Javier": {}, "Tom": {}},
    )
    simulation_builder.add_group_entity(
        "persons",
        ["Alicia", "Javier", "Tom"],
        households,
        {
            "housea": {"adults": ["Alicia"]},
            "houseb": {"adults": ["Tom"], "children": ["Javier"]},
        },
    )
    simulation_builder.register_variable("salary", persons)
    simulation_builder.add_parallel_axis(
        {"count": 2, "name": "salary", "min": 0, "max": 3000, "period": "2018-11"},
    )
    simulation_builder.expand_axes()
    assert [role.key for role in simulation_builder.get_roles("households")] == [
        "adult",
        "child",
        "adult",
        "adult",
        "child",
        "adult",
    ]


def test_add_axis_distributes_memberships(persons, households) -> None:
    simulation_builder = SimulationBuilder()
    simulation_builder.add_person_entity(
        persons,
        {"Alicia": {}, "Javier": {}, "Tom": {}},
    )
    simulation_builder.add_group_entity(
        "persons",
        ["Alicia", "Javier", "Tom"],
        households,
        {
            "housea": {"adults": ["Alicia"]},
            "houseb": {"adults": ["Tom"], "children": ["Javier"]},
        },
    )
    simulation_builder.register_variable("rent", households)
    simulation_builder.add_parallel_axis(
        {"count": 2, "name": "rent", "min": 0, "max": 3000, "period": "2018-11"},
    )
    simulation_builder.expand_axes()
    assert simulation_builder.get_memberships("households") == [0, 1, 1, 2, 3, 3]


def test_add_perpendicular_axes(persons) -> None:
    simulation_builder = SimulationBuilder()
    simulation_builder.add_person_entity(persons, {"Alicia": {}})
    simulation_builder.register_variable("salary", persons)
    simulation_builder.register_variable("pension", persons)
    simulation_builder.add_parallel_axis(
        {"count": 3, "name": "salary", "min": 0, "max": 3000, "period": "2018-11"},
    )
    simulation_builder.add_perpendicular_axis(
        {"count": 2, "name": "pension", "min": 0, "max": 2000, "period": "2018-11"},
    )
    simulation_builder.expand_axes()
    assert simulation_builder.get_input("salary", "2018-11") == pytest.approx(
        [0, 1500, 3000, 0, 1500, 3000],
    )
    assert simulation_builder.get_input("pension", "2018-11") == pytest.approx(
        [0, 0, 0, 2000, 2000, 2000],
    )


def test_add_perpendicular_axis_on_an_existing_variable_with_input(persons) -> None:
    simulation_builder = SimulationBuilder()
    simulation_builder.add_person_entity(
        persons,
        {
            "Alicia": {
                "salary": {"2018-11": 1000},
                "pension": {"2018-11": 1000},
            },
        },
    )
    simulation_builder.register_variable("salary", persons)
    simulation_builder.register_variable("pension", persons)
    simulation_builder.add_parallel_axis(
        {"count": 3, "name": "salary", "min": 0, "max": 3000, "period": "2018-11"},
    )
    simulation_builder.add_perpendicular_axis(
        {"count": 2, "name": "pension", "min": 0, "max": 2000, "period": "2018-11"},
    )
    simulation_builder.expand_axes()
    assert simulation_builder.get_input("salary", "2018-11") == pytest.approx(
        [0, 1500, 3000, 0, 1500, 3000],
    )
    assert simulation_builder.get_input("pension", "2018-11") == pytest.approx(
        [0, 0, 0, 2000, 2000, 2000],
    )


# Integration tests


def test_simulation_with_axes(tax_benefit_system) -> None:
    input_yaml = """
        persons:
          Alicia: {salary: {2018-11: 0}}
          Javier: {}
          Tom: {}
        households:
          housea:
            adults: [Alicia, Javier]
          houseb:
            adults: [Tom]
        axes:
            -
                - count: 2
                  name: rent
                  min: 0
                  max: 3000
                  period: 2018-11
    """
    data = test_runner.yaml.safe_load(input_yaml)
    simulation = SimulationBuilder().build_from_dict(tax_benefit_system, data)
    assert simulation.get_array("salary", "2018-11") == pytest.approx(
        [0, 0, 0, 0, 0, 0],
    )
    assert simulation.get_array("rent", "2018-11") == pytest.approx([0, 0, 3000, 0])


# Test for missing group entities with build_from_entities()


def test_simulation_with_axes_missing_entities(tax_benefit_system) -> None:
    input_yaml = """
        persons:
          Alicia: {salary: {2018-11: 0}}
          Javier: {}
          Tom: {}
        axes:
            -
                - count: 2
                  name: rent
                  min: 0
                  max: 3000
                  period: 2018-11
    """
    data = test_runner.yaml.safe_load(input_yaml)
    with pytest.raises(errors.SituationParsingError) as error:
        SimulationBuilder().build_from_dict(tax_benefit_system, data)
        assert "In order to expand over axes" in error.value()
        assert "all group entities and roles must be fully specified" in error.value()
