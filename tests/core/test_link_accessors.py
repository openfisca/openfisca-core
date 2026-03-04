import numpy
import pytest

from openfisca_core import entities, periods, taxbenefitsystems, variables
from openfisca_core.links.implicit import ImplicitMany2OneLink, ImplicitOne2ManyLink
from openfisca_core.simulations import SimulationBuilder


@pytest.fixture
def simple_sim():
    # two households, variable salaries on persons, roles for persons
    person = entities.SingleEntity("person", "persons", "A person", "")
    household = entities.GroupEntity(
        "household",
        "households",
        "A household",
        "",
        roles=[{"key": "parent"}, {"key": "child"}],
    )

    tbs = taxbenefitsystems.TaxBenefitSystem([person, household])

    class salary(variables.Variable):
        value_type = float
        entity = person
        definition_period = periods.DateUnit.YEAR

    class rent(variables.Variable):
        value_type = float
        entity = household
        definition_period = periods.DateUnit.YEAR

    tbs.add_variable(salary)
    tbs.add_variable(rent)

    sim = SimulationBuilder().build_from_dict(
        tbs,
        {
            "persons": {
                "p0": {"salary": {"2024": 1000.0}},
                "p1": {"salary": {"2024": 500.0}},
                "p2": {"salary": {"2024": 2000.0}},
                "p3": {"salary": {"2024": 100.0}},
            },
            "households": {
                "h0": {"parent": ["p0"], "child": ["p1"], "rent": {"2024": 800.0}},
                "h1": {"parent": ["p2"], "child": [], "rent": {"2024": 500.0}},
                "h2": {"parent": [], "child": ["p3"], "rent": {"2024": 100.0}},
            },
        },
    )
    return sim


def test_nth_accessor(simple_sim):
    link = ImplicitOne2ManyLink("persons", "household")
    link.attach(simple_sim.populations["household"])
    link.resolve(simple_sim.populations)

    # salaries grouped by household: h0->[p0(1000),p1(500)], h1->[p2(2000)], h2->[p3(100)]
    first = link.nth(0, "salary", "2024")
    assert numpy.array_equal(first, [1000.0, 2000.0, 100.0])

    second = link.nth(1, "salary", "2024")
    # only h0 has second member
    assert numpy.array_equal(second, [500.0, 0.0, 0.0])


def test_one2many_get_by_role(simple_sim):
    link = ImplicitOne2ManyLink("persons", "household")
    link.attach(simple_sim.populations["household"])
    link.resolve(simple_sim.populations)

    rents_parent = link.get_by_role("salary", "2024", role_value="parent")
    # salary of parent in each household: h0->1000, h1->2000, h2->0
    assert numpy.array_equal(rents_parent, [1000.0, 2000.0, 0.0])


def test_get_by_role(simple_sim):
    # use implicit many2one to fetch household rent per person using role
    many = ImplicitMany2OneLink("household")
    many.attach(simple_sim.persons)
    many.resolve(simple_sim.populations)

    # we expect parent/child roles available on person side
    rents_parent = many.get_by_role("rent", "2024", role_value="parent")
    # p0 is parent in h0 -> 800, p2 parent in h1 -> 500, others no parent
    assert numpy.array_equal(rents_parent, [800.0, 0.0, 500.0, 0.0])

    rents_child = many.get_by_role("rent", "2024", role_value="child")
    # p1 child of h0 -> 800, p3 child h2 ->100
    assert numpy.array_equal(rents_child, [0.0, 800.0, 0.0, 100.0])
