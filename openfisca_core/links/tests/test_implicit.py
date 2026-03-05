"""Test Phase 3: Auto-generation and implicit links."""

import numpy
import pytest

from openfisca_core import entities, periods, taxbenefitsystems, variables
from openfisca_core.links.implicit import ImplicitMany2OneLink, ImplicitOne2ManyLink
from openfisca_core.simulations import SimulationBuilder


@pytest.fixture
def sim():
    person = entities.SingleEntity("person", "persons", "A person", "")
    household = entities.GroupEntity(
        "household", "households", "A household", "", roles=[{"key": "member"}]
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

    for var in [salary, rent]:
        tbs.add_variable(var)

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
                "h0": {"member": ["p0", "p1"], "rent": {"2024": 800.0}},
                "h1": {"member": ["p2"], "rent": {"2024": 500.0}},
                "h2": {"member": ["p3"], "rent": {"2024": 100.0}},
            },
        },
    )
    return sim


def test_implicit_many2one(sim):
    link = ImplicitMany2OneLink("household")
    link.attach(sim.persons)
    link.resolve(sim.populations)

    rents = link.get("rent", "2024")
    # p0, p1 -> h0 -> 800
    # p2     -> h1 -> 500
    # p3     -> h2 -> 100
    assert numpy.array_equal(rents, [800.0, 800.0, 500.0, 100.0])


def test_implicit_one2many(sim):
    link = ImplicitOne2ManyLink("persons", "household", "person")
    link.attach(sim.populations["household"])
    link.resolve(sim.populations)

    salaries = link.sum("salary", "2024")
    # h0: p0+p1 = 1500
    # h1: p2 = 2000
    # h2: p3 = 100
    assert numpy.array_equal(salaries, [1500.0, 2000.0, 100.0])

    counts = link.count("2024")
    assert numpy.array_equal(counts, [2, 1, 1])


def test_implicit_one2many_with_non_default_person_key():
    """Regression test: entity key != 'person' must not crash.

    openfisca-france uses 'individu' as the person entity key.
    Before the fix, ImplicitOne2ManyLink hardcoded target_entity_key='person',
    causing a KeyError during link resolution.
    """
    individu = entities.SingleEntity("individu", "individus", "Un individu", "")
    menage = entities.GroupEntity(
        "menage",
        "menages",
        "Un ménage",
        "",
        roles=[{"key": "personne_de_reference"}],
    )

    tbs = taxbenefitsystems.TaxBenefitSystem([individu, menage])

    class salaire(variables.Variable):
        value_type = float
        entity = individu
        definition_period = periods.DateUnit.YEAR

    tbs.add_variable(salaire)

    sim = SimulationBuilder().build_from_dict(
        tbs,
        {
            "individus": {
                "i0": {"salaire": {"2024": 1000.0}},
                "i1": {"salaire": {"2024": 500.0}},
            },
            "menages": {
                "m0": {"personne_de_reference": ["i0", "i1"]},
            },
        },
    )

    # The implicit O2M link should resolve with target_entity_key='individu'
    link = ImplicitOne2ManyLink("individus", "menage", "individu")
    link.attach(sim.populations["menage"])
    link.resolve(sim.populations)  # Would raise KeyError before the fix

    salaires = link.sum("salaire", "2024")
    assert numpy.array_equal(salaires, [1500.0])


def test_implicit_m2o_role_projector_projected_to_persons():
    """person.group.projector('var', period) must return one value per person (projected).

    When using an implicit M2O link and a projector (e.g. .first_person or
    .demandeur), the result is at group level. It must be projected back to
    the source (person) level so each person gets their group's value.
    Regression test for projection being skipped when the projector has no
    'projectable' attribute (Projector instances).
    """
    person = entities.SingleEntity("person", "persons", "A person", "")
    household = entities.GroupEntity(
        "household", "households", "A household", "", roles=[{"key": "member"}]
    )

    tbs = taxbenefitsystems.TaxBenefitSystem([person, household])

    class age(variables.Variable):
        value_type = int
        entity = person
        definition_period = periods.DateUnit.YEAR

    class rent(variables.Variable):
        value_type = float
        entity = household
        definition_period = periods.DateUnit.YEAR

    for var in [age, rent]:
        tbs.add_variable(var)

    sim = SimulationBuilder().build_from_dict(
        tbs,
        {
            "persons": {
                "p0": {"age": {"2024": 40}},
                "p1": {"age": {"2024": 37}},
                "p2": {"age": {"2024": 54}},
                "p3": {"age": {"2024": 20}},
            },
            "households": {
                "h0": {"member": ["p0", "p1"], "rent": {"2024": 800.0}},
                "h1": {"member": ["p2", "p3"], "rent": {"2024": 500.0}},
            },
        },
    )

    # person.household.first_person('age', period) = first member's age per household,
    # projected to persons. p0,p1 in h0 (first p0=40) -> [40, 40]; p2,p3 in h1 (first p2=54) -> [54, 54]
    age_first = sim.persons.household.first_person("age", "2024")
    assert age_first.shape == (4,), "Result must be projected to person count"
    assert numpy.array_equal(age_first, [40, 40, 54, 54])


def test_implicit_m2o_project_entity_sized_same_as_old_logic():
    """Entity-sized result is projected: behaviour unchanged from old logic.

    When a projector (e.g. first_person) returns one value per entity,
    _project_implicit must project it to source (person) so each person
    gets their entity's value — same as target.project(result).
    """
    person = entities.SingleEntity("person", "persons", "A person", "")
    household = entities.GroupEntity(
        "household", "households", "A household", "", roles=[{"key": "member"}]
    )
    tbs = taxbenefitsystems.TaxBenefitSystem([person, household])

    class age(variables.Variable):
        value_type = int
        entity = person
        definition_period = periods.DateUnit.YEAR

    tbs.add_variable(age)

    sim = SimulationBuilder().build_from_dict(
        tbs,
        {
            "persons": {
                "p0": {"age": {"2024": 40}},
                "p1": {"age": {"2024": 37}},
                "p2": {"age": {"2024": 54}},
                "p3": {"age": {"2024": 20}},
            },
            "households": {
                "h0": {"member": ["p0", "p1"]},
                "h1": {"member": ["p2", "p3"]},
            },
        },
    )

    link = ImplicitMany2OneLink("household")
    link.attach(sim.persons)
    link.resolve(sim.populations)

    target = link._target_population
    # Entity-sized: 2 households -> 2 values
    entity_result = numpy.array([100.0, 200.0])
    assert entity_result.size == target.count

    projected = link._project_implicit(entity_result)
    # Old logic: target.project(result) -> each person gets their household's value
    expected = target.project(entity_result)
    assert numpy.array_equal(projected, expected)
    assert numpy.array_equal(projected, [100.0, 100.0, 200.0, 200.0])


def test_implicit_m2o_members_sized_returned_unchanged():
    """Members-sized result is returned as-is (regression for France maj_nbp).

    When a wrapped callable returns one value per member (e.g. like
    famille.members('activite') in openfisca-france), the result is already
    in source (person) space. Passing it to project() would raise
    InvalidArraySizeError. We must return it unchanged.
    """
    person = entities.SingleEntity("person", "persons", "A person", "")
    household = entities.GroupEntity(
        "household", "households", "A household", "", roles=[{"key": "member"}]
    )
    tbs = taxbenefitsystems.TaxBenefitSystem([person, household])

    class age(variables.Variable):
        value_type = int
        entity = person
        definition_period = periods.DateUnit.YEAR

    tbs.add_variable(age)

    sim = SimulationBuilder().build_from_dict(
        tbs,
        {
            "persons": {
                "p0": {"age": {"2024": 40}},
                "p1": {"age": {"2024": 37}},
                "p2": {"age": {"2024": 54}},
                "p3": {"age": {"2024": 20}},
            },
            "households": {
                "h0": {"member": ["p0", "p1"]},
                "h1": {"member": ["p2", "p3"]},
            },
        },
    )

    link = ImplicitMany2OneLink("household")
    link.attach(sim.persons)
    link.resolve(sim.populations)

    target = link._target_population
    # Members-sized: 4 persons -> 4 values (e.g. activite per person)
    members_result = numpy.array([10.0, 20.0, 30.0, 40.0])
    assert members_result.size == target.members.count

    out = link._project_implicit(members_result)
    assert out is members_result or numpy.array_equal(out, members_result)
    assert numpy.array_equal(out, [10.0, 20.0, 30.0, 40.0])


def test_implicit_m2o_project_implicit_rejects_wrong_size():
    """_project_implicit raises ValueError when result size matches neither entity nor members."""
    person = entities.SingleEntity("person", "persons", "A person", "")
    household = entities.GroupEntity(
        "household", "households", "A household", "", roles=[{"key": "member"}]
    )
    tbs = taxbenefitsystems.TaxBenefitSystem([person, household])
    sim = SimulationBuilder().build_from_dict(
        tbs,
        {
            "persons": {"p0": {}, "p1": {}},
            "households": {"h0": {"member": ["p0", "p1"]}},
        },
    )

    link = ImplicitMany2OneLink("household")
    link.attach(sim.persons)
    link.resolve(sim.populations)

    with pytest.raises(ValueError, match="result size .* does not match"):
        link._project_implicit(numpy.array([1.0, 2.0, 3.0]))  # size 3, neither 1 nor 2
