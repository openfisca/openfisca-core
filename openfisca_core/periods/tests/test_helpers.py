import pytest

from openfisca_core import periods
from openfisca_core.periods import Instant, Period
from openfisca_core.taxbenefitsystems import TaxBenefitSystem


@pytest.mark.parametrize("args", [
    TaxBenefitSystem,
    [2021, "-12"],
    "2021-31-12",
    "2021-foo",
    object,
    ])
def test_instant_with_invalid_arguments(args):
    """Raises a ValueError when called with invalid arguments."""

    with pytest.raises(ValueError, match = str(args)):
        periods.instant(args)


@pytest.mark.parametrize("actual, expected", [
    (periods.instant((2021, 9, 16)), Instant((2021, 9, 16))),
    (periods.instant(["2021", "9"]), Instant((2021, 9, 1))),
    (periods.instant(["2021", "09", "16"]), Instant((2021, 9, 16))),
    (periods.instant((2021, "9", "16")), Instant((2021, 9, 16))),
    (periods.instant((2021, 9, 16, 42)), Instant((2021, 9, 16))),
    (periods.instant("2021-09"), Instant((2021, 9, 1))),
    (periods.instant("2021-9-16"), Instant((2021, 9, 16))),
    (periods.instant("year:2021"), Instant((2021, 1, 1))),
    (periods.instant("year:2021:1"), Instant((2021, 1, 1))),
    (periods.instant("month:2021-9:2"), Instant((2021, 9, 1))),
    ])
def test_instant(actual, expected):
    """It works :)."""

    assert actual == expected


def test_instant_date_deprecation():
    """Throws a deprecation warning when called."""

    with pytest.warns(DeprecationWarning):
        periods.instant_date()


@pytest.mark.parametrize("args", [
    TaxBenefitSystem,
    [2021, "-12"],
    "2021-31-12",
    "2021-foo",
    "day:2014",
    object,
    ])
def test_period_with_invalid_arguments(args):
    """Raises a ValueError when called with invalid arguments."""

    with pytest.raises(ValueError, match = str(args)):
        periods.period(args)


@pytest.mark.parametrize("actual, expected", [
    (
        periods.period("ETERNITY"),
        Period(('eternity', Instant((1, 1, 1)), float("inf"))),
        ),
    (
        periods.period("2014-2"),
        Period(('month', Instant((2014, 2, 1)), 1)),
        ),
    (
        periods.period("2014-02"),
        Period(('month', Instant((2014, 2, 1)), 1)),
        ),
    (
        periods.period("2014-02-02"),
        Period(('day', Instant((2014, 2, 2)), 1)),
        ),
    ])
def test_period(actual, expected):
    """It works :)."""

    assert actual == expected


def test_N__deprecation():
    """Throws a deprecation warning when called."""

    with pytest.warns(DeprecationWarning):
        periods.N_(object())
