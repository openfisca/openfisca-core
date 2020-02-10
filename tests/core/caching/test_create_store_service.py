from openfisca_core import caching


def test_create_memory_caching():
    result = caching.CreateStoreService("memory")()

    assert type(result) == caching.MemoryCaching


def test_create_persistent_caching():
    result = caching.CreateStoreService("persistent")("/tmp")

    assert type(result) == caching.PersistentCaching
