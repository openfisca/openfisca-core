from openfisca_core import caching
from openfisca_core import periods

import pytest


@pytest.fixture
def cache():
    return caching.EternalCaching()


@pytest.fixture
def specific_period():
    return periods.period("2020")


@pytest.fixture
def eternal_period():
    return periods.period(periods.ETERNITY)


def test_period(cache, specific_period, eternal_period):
    result = cache.period(specific_period)

    assert result == eternal_period
