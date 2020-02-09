from openfisca_core import caching


def test__init__():
    time = caching.ExactCaching()
    store = caching.MemoryCaching()

    result = caching.Cache(time, store)

    assert result
