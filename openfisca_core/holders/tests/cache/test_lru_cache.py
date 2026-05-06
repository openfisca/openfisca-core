from __future__ import annotations

import pytest

from ..._cache import _LRUCache as Cache


@pytest.fixture
def cache() -> Cache[int, str]:
    return Cache(maxsize=3)


def test_put_and_get(cache: Cache[int, str]) -> None:
    cache.put(1, "one")
    assert cache.get(1) == "one"


def test_get_missing_returns_none(cache: Cache[int, str]) -> None:
    assert cache.get(99) is None


def test_contains(cache: Cache[int, str]) -> None:
    cache.put(1, "one")
    assert 1 in cache
    assert 2 not in cache


def test_put_overwrites_existing(cache: Cache[int, str]) -> None:
    cache.put(1, "one")
    cache.put(1, "ONE")
    assert cache.get(1) == "ONE"
    assert len(list(cache.items())) == 1


def test_fifo_eviction_drops_oldest() -> None:
    cache: Cache[int, str] = Cache(maxsize=2)
    cache.put(1, "one")
    cache.put(2, "two")
    cache.put(3, "three")
    assert cache.get(1) is None
    assert cache.get(2) == "two"
    assert cache.get(3) == "three"


def test_fifo_eviction_respects_maxsize() -> None:
    cache: Cache[int, str] = Cache(maxsize=1)
    cache.put(1, "one")
    cache.put(2, "two")
    assert cache.get(1) is None
    assert cache.get(2) == "two"


def test_items_returns_insertion_order(cache: Cache[int, str]) -> None:
    cache.put(10, "ten")
    cache.put(20, "twenty")
    cache.put(30, "thirty")
    assert list(cache.items()) == [(10, "ten"), (20, "twenty"), (30, "thirty")]


def test_evict_removes_matching(cache: Cache[int, str]) -> None:
    cache.put(1, "one")
    cache.put(2, "two")
    cache.put(3, "three")
    cache.evict(lambda k: k >= 2)
    assert cache.get(1) == "one"
    assert cache.get(2) is None
    assert cache.get(3) is None


def test_evict_no_match_leaves_cache_intact(cache: Cache[int, str]) -> None:
    cache.put(1, "one")
    cache.put(2, "two")
    cache.evict(lambda k: k > 100)
    assert list(cache.items()) == [(1, "one"), (2, "two")]


def test_evict_all_removes_everything(cache: Cache[int, str]) -> None:
    cache.put(1, "one")
    cache.put(2, "two")
    cache.evict(lambda _: True)
    assert list(cache.items()) == []


def test_clear_empties_cache(cache: Cache[int, str]) -> None:
    cache.put(1, "one")
    cache.put(2, "two")
    cache.clear()
    assert cache.get(1) is None
    assert list(cache.items()) == []


def test_maxsize_zero_never_stores() -> None:
    cache: Cache[int, str] = Cache(maxsize=0)
    cache.put(1, "one")
    assert cache.get(1) is None


def test_put_after_clear_works(cache: Cache[int, str]) -> None:
    cache.put(1, "one")
    cache.clear()
    cache.put(2, "two")
    assert cache.get(2) == "two"
