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
