from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Generic, TypeVar

from collections import OrderedDict

from openfisca_core import types as t

_K = TypeVar("_K")
_V = TypeVar("_V")


class _FIFOCache(t.Cache[_K, _V], Generic[_K, _V]):
    """Bounded FIFO cache: the oldest entry is evicted when capacity is reached."""

    def __init__(self, maxsize: int) -> None:
        self._store: OrderedDict[_K, _V] = OrderedDict()
        self._maxsize = maxsize

    def put(self, key: _K, value: _V) -> None:
        self._store[key] = value

        if len(self._store) > self._maxsize:
            self._store.popitem(last=False)

    def get(self, key: _K) -> _V | None:
        return self._store.get(key)

    def __contains__(self, key: object) -> bool:
        return key in self._store

    def items(self) -> Iterable[tuple[_K, _V]]:
        return self._store.items()

    def evict(self, predicate: Callable[[_K], bool]) -> None:
        to_evict = [k for k in self._store if predicate(k)]

        for k in to_evict:
            del self._store[k]

    def clear(self) -> None:
        self._store.clear()


class _LRUCache(t.Cache[_K, _V], Generic[_K, _V]):
    """Bounded LRU cache: the least recently used entry is evicted when capacity is reached."""

    def __init__(self, maxsize: int) -> None:
        self._store: OrderedDict[_K, _V] = OrderedDict()
        self._maxsize = maxsize

    def put(self, key: _K, value: _V) -> None:
        if key in self._store:
            self._store.move_to_end(key)

        self._store[key] = value

        if len(self._store) > self._maxsize:
            self._store.popitem(last=False)

    def get(self, key: _K) -> _V | None:
        if key not in self._store:
            return None

        self._store.move_to_end(key)

        return self._store[key]

    def __contains__(self, key: object) -> bool:
        return key in self._store

    def items(self) -> Iterable[tuple[_K, _V]]:
        return self._store.items()

    def evict(self, predicate: Callable[[_K], bool]) -> None:
        to_evict = [k for k in self._store if predicate(k)]

        for k in to_evict:
            del self._store[k]

    def clear(self) -> None:
        self._store.clear()
