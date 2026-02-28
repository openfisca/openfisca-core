"""Tests for the as_of variable feature.

An as_of variable's value, once set at a given instant, persists forward in
time until explicitly overridden.  Values are stored as a base array +
sparse patches (changed indices/values only); the snapshot cursor makes
forward-sequential reads incremental.

Formulas and aggregations are completely unaware of the mechanism.
"""

from __future__ import annotations

import numpy
import pytest

from openfisca_core.entities import Entity
from openfisca_core.holders import Holder
from openfisca_core.periods import DateUnit, period
from openfisca_core.populations import Population
from openfisca_core.variables import Variable

# ---------------------------------------------------------------------------
# Minimal test fixtures – no country-template dependency
# ---------------------------------------------------------------------------

_entity = Entity("person", "persons", "", "")


class _AsOfIntVariable(Variable):
    """A simple integer variable that persists (as_of = 'start')."""

    entity = _entity
    definition_period = DateUnit.MONTH
    value_type = int
    as_of = "start"


class _AsOfEndVariable(Variable):
    """Same but uses the end-of-period convention."""

    entity = _entity
    definition_period = DateUnit.YEAR
    value_type = int
    as_of = "end"


class _RegularVariable(Variable):
    """A normal variable without as_of semantics."""

    entity = _entity
    definition_period = DateUnit.MONTH
    value_type = int


def _make_holder(variable_class, count=2):
    """Return a ready-to-use Holder with *count* individuals."""
    population = Population(_entity)
    population.simulation = None
    population.count = count
    return Holder(variable_class(), population)


# ---------------------------------------------------------------------------
# 1. Value persists forward in time
# ---------------------------------------------------------------------------


def test_asof_persists_forward():
    """Value set in Jan 2024 should be returned for Feb and Mar 2024."""
    holder = _make_holder(_AsOfIntVariable)
    holder.set_input("2024-01", numpy.array([10, 20]))

    for month in ("2024-02", "2024-03", "2024-06", "2024-12"):
        result = holder.get_array(period(month))
        numpy.testing.assert_array_equal(
            result,
            [10, 20],
            err_msg=f"Expected persisted value for {month}",
        )


# ---------------------------------------------------------------------------
# 2. No value stored before the first stored instant → None
# ---------------------------------------------------------------------------


def test_asof_no_value_before_first_stored():
    """get_array returns None for any period before the first stored instant."""
    holder = _make_holder(_AsOfIntVariable)
    holder.set_input("2024-06", numpy.array([1, 2]))

    assert holder.get_array(period("2024-01")) is None
    assert holder.get_array(period("2024-05")) is None


# ---------------------------------------------------------------------------
# 3. Exact match returns the correct value (via snapshot cursor)
# ---------------------------------------------------------------------------


def test_asof_exact_match_returns_stored_value():
    """get_array for the exact base period returns the base value."""
    holder = _make_holder(_AsOfIntVariable)
    holder.set_input("2024-03", numpy.array([7, 8]))

    result = holder.get_array(period("2024-03"))
    numpy.testing.assert_array_equal(result, [7, 8])


# ---------------------------------------------------------------------------
# 4. Most-recent stored value wins
# ---------------------------------------------------------------------------


def test_asof_takes_most_recent_value():
    """With two stored values, the one closest to (but not after) target wins."""
    holder = _make_holder(_AsOfIntVariable)
    holder.set_input("2024-01", numpy.array([1, 1]))
    holder.set_input("2024-04", numpy.array([4, 4]))

    # Before first stored instant → None
    assert holder.get_array(period("2023-12")) is None

    # At or after first, before second → first value
    for month in ("2024-01", "2024-02", "2024-03"):
        numpy.testing.assert_array_equal(
            holder.get_array(period(month)),
            [1, 1],
            err_msg=f"Expected first value for {month}",
        )

    # At or after second → second value
    for month in ("2024-04", "2024-05", "2025-01"):
        numpy.testing.assert_array_equal(
            holder.get_array(period(month)),
            [4, 4],
            err_msg=f"Expected second value for {month}",
        )


# ---------------------------------------------------------------------------
# 5. Convention: "start" vs "end" for a YEAR period
# ---------------------------------------------------------------------------


def test_asof_convention_start():
    """With as_of='start', a value set mid-year is NOT visible for that year."""
    holder = _make_holder(_AsOfIntVariable)  # definition_period=MONTH, as_of='start'
    holder.set_input("2024-06", numpy.array([99, 99]))

    # Period "2024-01" starts at 2024-01-01 < 2024-06-01 → None
    assert holder.get_array(period("2024-01")) is None
    # Period "2024-07" starts at 2024-07-01 > 2024-06-01 → visible
    numpy.testing.assert_array_equal(
        holder.get_array(period("2024-07")),
        [99, 99],
    )


def test_asof_convention_end():
    """With as_of='end', a value set mid-year IS visible for that year."""
    holder = _make_holder(_AsOfEndVariable)  # definition_period=YEAR, as_of='end'
    holder.set_input("2024", numpy.array([42, 42]))

    # Year 2024 ends 2024-12-31; our value is stored with start 2024-01-01
    # which is ≤ 2024-12-31 → visible
    numpy.testing.assert_array_equal(
        holder.get_array(period("2024")),
        [42, 42],
    )


# ---------------------------------------------------------------------------
# 6. Regular variable (no as_of) is unaffected
# ---------------------------------------------------------------------------


def test_non_asof_variable_unaffected():
    """A variable without as_of still returns None for unstored periods."""
    holder = _make_holder(_RegularVariable)
    holder.set_input("2024-01", numpy.array([5, 6]))

    # Exact match works
    numpy.testing.assert_array_equal(holder.get_array(period("2024-01")), [5, 6])
    # Other periods return None (no persistence)
    assert holder.get_array(period("2024-02")) is None
    assert holder.get_array(period("2023-12")) is None


# ---------------------------------------------------------------------------
<<<<<<< HEAD
# 7. Patch storage: only the diff is persisted
# ---------------------------------------------------------------------------


def test_asof_no_patch_when_value_unchanged():
    """When the new value is identical to the current state, no patch is stored."""
    holder = _make_holder(_AsOfIntVariable)
    holder.set_input("2024-01", numpy.array([3, 3]))  # base
    holder.set_input("2024-02", numpy.array([3, 3]))  # identical → no patch

    assert (
        len(holder._as_of_patches) == 0
    ), "No patch should be stored for unchanged values"


def test_asof_patch_stores_only_changed_indices():
    """A patch stores only the indices and values that actually changed."""
    holder = _make_holder(_AsOfIntVariable, count=3)
    holder.set_input("2024-01", numpy.array([1, 2, 3]))  # base
    holder.set_input("2024-04", numpy.array([1, 9, 3]))  # only person 1 changes

    assert len(holder._as_of_patches) == 1
    _, idx, vals = holder._as_of_patches[0]
    numpy.testing.assert_array_equal(idx, [1])
    numpy.testing.assert_array_equal(vals, [9])


def test_asof_retroactive_patch():
    """A set_input for a past instant is correctly reflected in all later GETs."""
    holder = _make_holder(_AsOfIntVariable)
    holder.set_input("2024-01", numpy.array([1, 2]))
    holder.set_input("2024-06", numpy.array([1, 9]))
    # Retroactively set a change at 2024-03 (before the 2024-06 patch)
    holder.set_input("2024-03", numpy.array([5, 2]))

    # Before 2024-03 patch: base only
    numpy.testing.assert_array_equal(holder.get_array(period("2024-02")), [1, 2])
    # Between 2024-03 and 2024-06: 2024-03 patch applied
    numpy.testing.assert_array_equal(holder.get_array(period("2024-04")), [5, 2])
    # After 2024-06: both patches applied
    numpy.testing.assert_array_equal(holder.get_array(period("2024-07")), [5, 9])


# ---------------------------------------------------------------------------
# 8. Snapshot cursor: sequential reads share array objects
# ---------------------------------------------------------------------------


def test_asof_snapshot_cursor_no_copy_between_patches():
    """Sequential GETs for periods with no patches between them reuse the same array."""
    holder = _make_holder(_AsOfIntVariable)
    holder.set_input("2024-01", numpy.array([1, 2]))  # base only, no patches

    r_feb = holder.get_array(period("2024-02"))
    r_mar = holder.get_array(period("2024-03"))
    assert r_feb is r_mar, "No patches between months → same snapshot array reused"


# ---------------------------------------------------------------------------
# 9. Stored arrays are read-only (mutation guard)
# ---------------------------------------------------------------------------


def test_asof_base_array_is_read_only():
    """The base array stored for an as_of variable must be read-only."""
    holder = _make_holder(_AsOfIntVariable)
    holder.set_input("2024-01", numpy.array([1, 2]))

    assert not holder._as_of_base.flags.writeable, "Base array should be read-only"


def test_asof_get_array_returns_read_only():
    """Arrays returned by get_array for as_of variables must be read-only."""
    holder = _make_holder(_AsOfIntVariable)
    holder.set_input("2024-01", numpy.array([1, 2]))
    holder.set_input("2024-04", numpy.array([3, 2]))  # patch

    for month in ("2024-01", "2024-03", "2024-05"):
        result = holder.get_array(period(month))
        assert (
            not result.flags.writeable
        ), f"Returned array for {month} should be read-only"


def test_asof_setting_value_does_not_mutate_caller_array():
    """set_input must not mark the *caller's* array as read-only."""
    holder = _make_holder(_AsOfIntVariable)
    caller_arr = numpy.array([10, 20])
    holder.set_input("2024-01", caller_arr)

    # The caller should still be able to write to their array
    caller_arr[0] = 99  # must not raise


# ---------------------------------------------------------------------------
# 9. Variable declaration validation
# ---------------------------------------------------------------------------


def test_as_of_true_normalises_to_start():
    """as_of=True is a documented alias for as_of='start'."""

    class MyVar(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = True

    assert MyVar().as_of == "start"


def test_as_of_false_default():
    """Variables without as_of declaration default to as_of=False."""

    class MyVar(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int

    assert MyVar().as_of is False


def test_as_of_invalid_value_raises():
    """as_of with an invalid value must raise ValueError at instantiation."""

    class MyVar(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "monthly"  # invalid

    with pytest.raises(ValueError, match="as_of"):
        MyVar()


def test_as_of_with_set_input_helper_raises():
    """Combining as_of with a set_input helper is explicitly forbidden."""
    from openfisca_core.holders import set_input_divide_by_period

    class MyVar(Variable):
        entity = _entity
        definition_period = DateUnit.MONTH
        value_type = int
        as_of = "start"
        set_input = set_input_divide_by_period

    with pytest.raises(ValueError, match="incompatible"):
        MyVar()
