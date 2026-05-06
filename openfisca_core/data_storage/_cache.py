from __future__ import annotations

from collections.abc import Callable, Iterable

from openfisca_core import periods, types as t


def _day_period(instant: t.Instant) -> t.Period:
    return periods.Period((periods.DAY, instant, 1))


class StorageCache(t.Cache[t.Instant, t.Snapshot]):
    """Cache adapter mapping Instant keys onto InMemoryStorage or OnDiskStorage.

    Instants are stored as single-day Periods so both storage backends work
    transparently.  Passing an OnDiskStorage lets snapshot arrays be offloaded
    to disk under memory pressure.
    """

    def __init__(self, storage: t.Storage) -> None:
        self._storage = storage
        self._patch_idxs: dict[t.Instant, int] = {}

    def put(self, key: t.Instant, value: t.Snapshot) -> None:
        """Store a snapshot for the given instant."""
        array, patch_idx = value
        self._storage.put(array, _day_period(key))
        self._patch_idxs[key] = patch_idx

    def get(self, key: t.Instant) -> t.Snapshot | None:
        """Return the snapshot for the given instant, or None if not cached."""
        if key not in self._patch_idxs:
            return None

        array = self._storage.get(_day_period(key))

        if array is None:
            return None

        return (array, self._patch_idxs[key])

    def __contains__(self, key: object) -> bool:
        return key in self._patch_idxs

    def items(self) -> Iterable[tuple[t.Instant, t.Snapshot]]:
        """Yield all (instant, snapshot) pairs currently in the cache."""
        for instant, patch_idx in self._patch_idxs.items():
            array = self._storage.get(_day_period(instant))

            if array is not None:
                yield instant, (array, patch_idx)

    def evict(self, predicate: Callable[[t.Instant], bool]) -> None:
        """Remove all entries whose instant satisfies predicate."""
        to_evict = [k for k in self._patch_idxs if predicate(k)]

        for k in to_evict:
            self._storage.delete(_day_period(k))
            del self._patch_idxs[k]

    def clear(self) -> None:
        """Remove all entries from the cache and the backing storage."""
        for k in list(self._patch_idxs):
            self._storage.delete(_day_period(k))

        self._patch_idxs.clear()
