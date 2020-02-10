from openfisca_core import caching
from openfisca_core import periods

import pytest


@pytest.fixture
def exact():
    return periods.period("2020")


@pytest.fixture
def eternal():
    return periods.period(periods.ETERNITY)


def test_create_exact_caching(exact):
    result = caching.CreateTimeService(exact)()

    assert type(result) == caching.ExactCaching


def test_create_eternal_caching(eternal):
    result = caching.CreateTimeService(eternal)()

    assert type(result) == caching.EternalCaching
