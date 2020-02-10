from openfisca_core import caching


def test__init__():
    timeness = caching.ExactCaching()
    storage = caching.MemoryCaching()

    result = caching.Cache(timeness, storage)

    assert result
