"""Tests for the as_of variable feature.

An as_of variable's value, once set at a given instant, persists forward in
time until explicitly overridden.  The semantics live entirely in
``Holder.get_array`` / ``_get_as_of``; formulas and aggregations are
completely unaware of the mechanism.
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
# 3. Exact match still works (takes priority via memory lookup)
# ---------------------------------------------------------------------------


def test_asof_exact_match_returns_stored_value():
    """Exact period lookup hits the fast path and skips _get_as_of."""
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
# 7. Reference sharing: identical consecutive values share the same object
# ---------------------------------------------------------------------------


def test_asof_reference_sharing():
    """When the value does not change, the same array object is stored."""
    holder = _make_holder(_AsOfIntVariable)
    holder.set_input("2024-01", numpy.array([3, 3]))
    holder.set_input("2024-02", numpy.array([3, 3]))  # same values

    arr_jan = holder._memory_storage.get(period("2024-01"))
    arr_feb = holder._memory_storage.get(period("2024-02"))
    assert arr_jan is arr_feb, "Identical values should share the same array object"


# ---------------------------------------------------------------------------
# 8. Stored arrays are read-only (mutation guard)
# ---------------------------------------------------------------------------


def test_asof_stored_array_is_read_only():
    """Arrays stored for as_of variables must be read-only."""
    holder = _make_holder(_AsOfIntVariable)
    holder.set_input("2024-01", numpy.array([1, 2]))

    stored = holder._memory_storage.get(period("2024-01"))
    assert not stored.flags.writeable, "Stored as_of array should be read-only"


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
