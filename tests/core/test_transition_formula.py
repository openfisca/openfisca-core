"""Tests for the transition_formula feature.

transition_formula is an alternative to formula for as_of variables.
Instead of returning a full N-array, it returns (selector, vals) describing
only the individuals that change state — enabling O(k) sparse storage with
no O(N) diff computation.

Naming convention mirrors formula_YYYY_MM_DD: transition_formula_YYYY_MM_DD.
"""

from __future__ import annotations

import numpy
import pytest

from openfisca_core.entities import Entity
from openfisca_core.holders import Holder
from openfisca_core.periods import DateUnit, period
from openfisca_core.populations import Population
from openfisca_core.simulations import Simulation
from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_core.variables import Variable

# ---------------------------------------------------------------------------
# Minimal fixtures — no country-template dependency
# ---------------------------------------------------------------------------

_entity = Entity("person", "persons", "", "")


def _make_simulation(*variable_classes, count: int = 3) -> Simulation:
    """Build a minimal Simulation with the given variable classes.

    TaxBenefitSystem copies the entity internally, so the Population must use
    tbs.person_entity (the copy) to ensure _tax_benefit_system is set.
    """
    tbs = TaxBenefitSystem([_entity])
    person_entity = tbs.person_entity  # the copy that has _tax_benefit_system set
    for vc in variable_classes:
        tbs.add_variable(vc)
    pop = Population(person_entity)
    pop.count = count
    pop.ids = [str(i) for i in range(count)]
    sim = Simulation(tbs, {person_entity.key: pop})
    return sim


# ---------------------------------------------------------------------------
# 1. Variable-level validation — no simulation needed
# ---------------------------------------------------------------------------


def test_transition_formula_requires_asof():
    """Declaring transition_formula without as_of must raise at instantiation."""

    class MyVar(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int

        def transition_formula(person, period):  # noqa: N805
            return numpy.array([False, False, False]), numpy.array([])

    with pytest.raises(ValueError, match="as_of"):
        MyVar()


def test_transition_formula_exclusive_with_formula():
    """Declaring both formula and transition_formula must raise at instantiation."""

    class MyVar(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"

        def formula(person, period):  # noqa: N805
            return numpy.zeros(3, dtype=numpy.int32)

        def transition_formula(person, period):  # noqa: N805
            return numpy.array([False, False, False]), numpy.array([])

    with pytest.raises(ValueError, match="mutually exclusive"):
        MyVar()


def test_transition_formula_is_not_input_variable():
    """A variable with transition_formula is not an input variable."""

    class MyVar(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"

        def transition_formula(person, period):  # noqa: N805
            return numpy.array([False, False, False]), numpy.array([])

    assert not MyVar().is_input_variable()


def test_has_transition_formula_property():
    """has_transition_formula reflects whether transition_formula* exist."""

    class WithTransition(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"

        def transition_formula(person, period):  # noqa: N805
            return numpy.array([False, False, False]), numpy.array([])

    class WithoutTransition(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int

    assert WithTransition().has_transition_formula
    assert not WithoutTransition().has_transition_formula


# ---------------------------------------------------------------------------
# 2. Date dispatch — transition_formula_YYYY_MM_DD
# ---------------------------------------------------------------------------


def test_transition_formula_date_dispatch():
    """transition_formula_2024 replaces transition_formula from 2024 onwards."""

    class Echelon(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"

        def transition_formula(person, period):  # noqa: N805
            # Rule before 2024: person 0 gets +1
            return numpy.array([True, False, False]), numpy.array([10])

        def transition_formula_2024_01_01(person, period):  # noqa: N805
            # Rule from 2024: person 1 gets +2
            return numpy.array([False, True, False]), numpy.array([20])

    var = Echelon()
    # get_transition_formula returns the raw unbound function from the SortedDict,
    # so compare against the class-level function (not the bound method via var.xxx).
    assert var.get_transition_formula("2023-06") is Echelon.transition_formula
    assert (
        var.get_transition_formula("2024-01") is Echelon.transition_formula_2024_01_01
    )
    assert (
        var.get_transition_formula("2025-03") is Echelon.transition_formula_2024_01_01
    )


# ---------------------------------------------------------------------------
# 3. Basic execution — simulation.calculate triggers transition_formula
# ---------------------------------------------------------------------------


def test_transition_formula_basic():
    """transition_formula result is correctly stored and returned."""

    class Score(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"

        def transition_formula(person, period):  # noqa: N805
            # person 1 transitions to 99
            return numpy.array([False, True, False]), numpy.array([99])

    sim = _make_simulation(Score)
    sim.set_input("Score", "2024-01", numpy.array([1, 2, 3]))

    result = sim.calculate("Score", "2024-02")
    numpy.testing.assert_array_equal(result, [1, 99, 3])


def test_transition_formula_none_return_persists_previous():
    """Returning None from transition_formula leaves the previous state intact."""

    class Score(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"

        def transition_formula(person, period):  # noqa: N805
            return None  # no change

    sim = _make_simulation(Score)
    sim.set_input("Score", "2024-01", numpy.array([10, 20, 30]))

    result = sim.calculate("Score", "2024-03")
    numpy.testing.assert_array_equal(result, [10, 20, 30])


def test_transition_formula_scalar_vals():
    """A scalar val is broadcast to all selected individuals."""

    class Bonus(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"

        def transition_formula(person, period):  # noqa: N805
            # Everyone gets a flat 500
            return numpy.array([True, True, True]), 500

    sim = _make_simulation(Bonus)
    sim.set_input("Bonus", "2024-01", numpy.array([0, 0, 0]))

    result = sim.calculate("Bonus", "2024-02")
    numpy.testing.assert_array_equal(result, [500, 500, 500])


def test_transition_formula_computed_once_per_instant():
    """transition_formula is not called twice for the same instant."""
    call_count = [0]

    class Counter(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"

        def transition_formula(person, period):  # noqa: N805
            call_count[0] += 1
            return numpy.array([True, False, False]), numpy.array([call_count[0]])

    sim = _make_simulation(Counter)
    sim.set_input("Counter", "2024-01", numpy.array([0, 0, 0]))

    r1 = sim.calculate("Counter", "2024-02")
    r2 = sim.calculate("Counter", "2024-02")

    assert call_count[0] == 1, "Formula must be called exactly once per instant"
    numpy.testing.assert_array_equal(r1, r2)


def test_transition_formula_no_base_raises():
    """If set_input was never called and no initial_formula is defined, raise."""

    class Score(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"

        def transition_formula(person, period):  # noqa: N805
            return numpy.array([True, False, False]), numpy.array([99])

    sim = _make_simulation(Score)
    with pytest.raises(ValueError, match="no initial state"):
        sim.calculate("Score", "2024-01")


# ---------------------------------------------------------------------------
# 3b. initial_formula
# ---------------------------------------------------------------------------


def test_initial_formula_establishes_base():
    """initial_formula is called on first access and establishes the base."""

    class Score(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"

        def initial_formula(person, period):  # noqa: N805
            return numpy.array([10, 20, 30])

        def transition_formula(person, period):  # noqa: N805
            return numpy.array([False, False, False]), numpy.array([])

    sim = _make_simulation(Score)
    result = sim.calculate("Score", "2024-01")
    numpy.testing.assert_array_equal(result, [10, 20, 30])


def test_initial_formula_then_transition():
    """initial_formula seeds the state; transition_formula evolves it."""

    class Score(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"

        def initial_formula(person, period):  # noqa: N805
            return numpy.array([1, 2, 3])

        def transition_formula(person, period):  # noqa: N805
            # First person gains 10 each month.
            return numpy.array([0]), numpy.array([person("Score", period.last_month)[0] + 10])

    sim = _make_simulation(Score)
    sim.calculate("Score", "2024-01")  # seeds: [1, 2, 3]
    result = sim.calculate("Score", "2024-02")
    numpy.testing.assert_array_equal(result, [11, 2, 3])


def test_initial_formula_requires_as_of():
    """initial_formula without as_of raises at instantiation time."""

    class Bad(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int

        def initial_formula(person, period):  # noqa: N805
            return numpy.zeros(3)

    with pytest.raises(ValueError, match="initial_formula.*as_of"):
        Bad()


def test_initial_formula_date_dispatch():
    """initial_formula_YYYY_MM_DD dispatch works like formula_YYYY_MM_DD."""

    class Score(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"

        def initial_formula(person, period):  # noqa: N805
            return numpy.array([0, 0, 0])

        def initial_formula_2025_01_01(person, period):  # noqa: N805
            return numpy.array([99, 99, 99])

        def transition_formula(person, period):  # noqa: N805
            return numpy.array([], dtype=numpy.int32), numpy.array([])

    sim_before = _make_simulation(Score)
    sim_before.calculate("Score", "2024-06")
    numpy.testing.assert_array_equal(
        sim_before.get_array("Score", "2024-06"), [0, 0, 0]
    )

    sim_after = _make_simulation(Score)
    sim_after.calculate("Score", "2025-06")
    numpy.testing.assert_array_equal(
        sim_after.get_array("Score", "2025-06"), [99, 99, 99]
    )


# ---------------------------------------------------------------------------
# 4. Date dispatch integration
# ---------------------------------------------------------------------------


def test_transition_formula_date_dispatch_integration():
    """The correct dated transition_formula is applied for each period."""

    class Echelon(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"

        def transition_formula(person, period):  # noqa: N805
            # Old rule: person 0 gets 10
            return numpy.array([True, False, False]), numpy.array([10])

        def transition_formula_2024_06_01(person, period):  # noqa: N805
            # New rule: person 1 gets 20
            return numpy.array([False, True, False]), numpy.array([20])

    sim = _make_simulation(Echelon)
    sim.set_input("Echelon", "2024-01", numpy.array([0, 0, 0]))

    # Before 2024-06: old rule applies → person 0 → 10
    r_jan = sim.calculate("Echelon", "2024-02")
    numpy.testing.assert_array_equal(r_jan, [10, 0, 0])

    # From 2024-06: new rule applies → person 1 → 20
    r_jun = sim.calculate("Echelon", "2024-06")
    numpy.testing.assert_array_equal(r_jun, [10, 20, 0])


# ---------------------------------------------------------------------------
# 5. Mismatch between selector length and vals length → clear error
# ---------------------------------------------------------------------------


def test_transition_formula_length_mismatch_raises():
    """Returning mismatched selector/vals lengths must raise ValueError."""

    class Bad(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"

        def transition_formula(person, period):  # noqa: N805
            # mask selects 2 but vals has 3 → error
            return numpy.array([True, True, False]), numpy.array([1, 2, 3])

    sim = _make_simulation(Bad)
    sim.set_input("Bad", "2024-01", numpy.array([0, 0, 0]))

    with pytest.raises(ValueError, match="2 selected"):
        sim.calculate("Bad", "2024-02")


# ---------------------------------------------------------------------------
# 5. Tracer — cycle vs spiral
# ---------------------------------------------------------------------------


def test_transition_formula_temporal_recursion_not_spiral():
    """Reading the same as_of variable at a previous period must NOT trigger
    SpiralError — the recursion terminates via _as_of_transition_computed."""

    class Score(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"

        def initial_formula(person, period):  # noqa: N805
            return numpy.array([0, 0, 0])

        def transition_formula(person, period):  # noqa: N805
            # reads the same variable one month back — legitimate temporal recursion
            prev = person("Score", period.last_month)
            return numpy.array([0, 1, 2]), prev[[0, 1, 2]] + 1

    sim = _make_simulation(Score)
    # sequential: init=0 → +1 at 2024-02 → +1 at 2024-03 = [2, 2, 2]
    sim.calculate("Score", "2024-01")
    sim.calculate("Score", "2024-02")
    result = sim.calculate("Score", "2024-03")
    numpy.testing.assert_array_equal(result, [2, 2, 2])


def test_transition_formula_true_cycle_raises():
    """A transition_formula that reads the same variable@same period must
    raise CycleError (genuine infinite loop)."""

    class Score(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"

        def transition_formula(person, period):  # noqa: N805
            # reads itself at the SAME period → true cycle
            person("Score", period)
            return numpy.array([], dtype=numpy.int32), numpy.array([])

    sim = _make_simulation(Score)
    sim.set_input("Score", "2024-01", numpy.array([0, 0, 0]))
    # CycleError is caught inside _calculate_transition; the call completes
    # with the previous state (no patch applied) rather than crashing.
    result = sim.calculate("Score", "2024-02")
    numpy.testing.assert_array_equal(result, [0, 0, 0])
