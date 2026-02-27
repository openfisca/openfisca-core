import numpy as np

from openfisca_core import entities, periods, taxbenefitsystems
from openfisca_core.entities.entity import Entity
from openfisca_core.populations._core_population import CorePopulation
from openfisca_core.simulations import SimulationBuilder


def test_get_period_id_to_rownum_remapping():
    # Setup entity and population
    entity = Entity("person", "people", "", "")
    pop = CorePopulation(entity)
    pop.count = 3

    # initial mapping: identity (0->0,1->1,2->2)
    pop._id_to_rownum = np.array([0, 1, 2], dtype=np.intp)
    t0 = periods.period("2010-01")
    pop.snapshot_period(t0)

    # change mapping to simulate reordering/new indexing
    # now id 0 -> row 2, id 1 -> row 0, id 2 -> row 1
    pop._id_to_rownum = np.array([2, 0, 1], dtype=np.intp)
    t1 = periods.period("2010-02")
    pop.snapshot_period(t1)

    # ids to remap (as stored in data referring to t0)
    ids = np.array([0, 0, 1, 2, 0], dtype=np.intp)

    past_index = pop.get_period_id_to_rownum(t0)
    assert past_index is not None
    rows_t0 = past_index[ids]
    # with identity mapping, rows should equal the ids
    assert np.array_equal(rows_t0, np.array([0, 0, 1, 2, 0], dtype=np.intp))

    # current mapping produces different rows
    current_index = pop.get_period_id_to_rownum(t1)
    assert current_index is not None
    rows_t1 = current_index[ids]
    assert np.array_equal(rows_t1, np.array([2, 2, 0, 1, 2], dtype=np.intp))


def _make_tbs():
    """Return a minimal TaxBenefitSystem with one person entity."""
    person = entities.Entity("person", "persons", "", "")
    return taxbenefitsystems.TaxBenefitSystem([person])


def _make_group_tbs():
    """Return a TaxBenefitSystem with a person and a group entity."""
    person = entities.SingleEntity("person", "persons", "", "")
    household = entities.GroupEntity(
        "household", "households", "", "", roles=[{"key": "member"}]
    )
    return taxbenefitsystems.TaxBenefitSystem([person, household])


def test_build_default_simulation_sets_id_to_rownum():
    """SimulationBuilder.build_default_simulation populates _id_to_rownum."""
    tbs = _make_tbs()
    sim = SimulationBuilder().build_default_simulation(tbs, count=3)
    for pop in sim.populations.values():
        assert pop._id_to_rownum is not None
        assert np.array_equal(pop._id_to_rownum, np.arange(3, dtype=np.intp))


def test_build_from_dict_sets_id_to_rownum():
    """SimulationBuilder.build_from_dict populates _id_to_rownum."""
    tbs = _make_tbs()
    sim = SimulationBuilder().build_from_dict(
        tbs,
        {
            "persons": {
                "p0": {},
                "p1": {},
                "p2": {},
            },
        },
    )
    pop = sim.populations["person"]
    assert pop._id_to_rownum is not None
    assert np.array_equal(pop._id_to_rownum, np.arange(3, dtype=np.intp))


def test_build_default_simulation_empty():
    """count=0 produces an empty identity mapping, not None."""
    tbs = _make_tbs()
    sim = SimulationBuilder().build_default_simulation(tbs, count=0)
    for pop in sim.populations.values():
        assert pop._id_to_rownum is not None
        assert pop._id_to_rownum.shape == (0,)
        assert pop._id_to_rownum.dtype == np.intp


def test_build_default_simulation_single():
    """count=1 produces a single-element identity mapping."""
    tbs = _make_tbs()
    sim = SimulationBuilder().build_default_simulation(tbs, count=1)
    for pop in sim.populations.values():
        assert np.array_equal(pop._id_to_rownum, np.array([0], dtype=np.intp))


def test_build_default_simulation_group_tbs_both_populations():
    """Both person and group populations receive _id_to_rownum."""
    tbs = _make_group_tbs()
    sim = SimulationBuilder().build_default_simulation(tbs, count=2)
    assert np.array_equal(sim.populations["person"]._id_to_rownum, [0, 1])
    assert np.array_equal(sim.populations["household"]._id_to_rownum, [0, 1])


def test_build_from_dict_group_tbs_both_populations():
    """build_from_dict sets _id_to_rownum on both person and group populations."""
    tbs = _make_group_tbs()
    sim = SimulationBuilder().build_from_dict(
        tbs,
        {
            "persons": {"p0": {}, "p1": {}, "p2": {}},
            "households": {
                "h0": {"member": ["p0", "p1"]},
                "h1": {"member": ["p2"]},
            },
        },
    )
    assert np.array_equal(
        sim.populations["person"]._id_to_rownum, np.arange(3, dtype=np.intp)
    )
    assert np.array_equal(
        sim.populations["household"]._id_to_rownum, np.arange(2, dtype=np.intp)
    )


def test_id_to_rownum_dtype():
    """_id_to_rownum always has dtype numpy.intp."""
    tbs = _make_tbs()
    sim = SimulationBuilder().build_default_simulation(tbs, count=4)
    pop = sim.populations["person"]
    assert pop._id_to_rownum.dtype == np.intp


def test_id_to_rownum_usable_as_index():
    """_id_to_rownum identity mapping round-trips: rownum[id] == id."""
    tbs = _make_tbs()
    count = 5
    sim = SimulationBuilder().build_default_simulation(tbs, count=count)
    pop = sim.populations["person"]
    ids = np.arange(count, dtype=np.intp)
    assert np.array_equal(pop._id_to_rownum[ids], ids)
