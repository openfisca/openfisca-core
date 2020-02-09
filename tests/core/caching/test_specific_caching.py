from openfisca_core import caching
from openfisca_core import periods

import pytest


@pytest.fixture
def cache():
    return caching.SpecificCaching()


@pytest.fixture
def period():
    return periods.period("2020")


def test_period(cache, period):
    result = cache.period(period)

    assert result == period
