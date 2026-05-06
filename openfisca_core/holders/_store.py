from __future__ import annotations

import bisect

import numpy

from openfisca_core import data_storage, types as t

from ._cache import _FIFOCache


class _TemporalStore(t.Store):
    """Shared temporal event-sourced store logic.

    Stores a read-only base array and a sorted list of sparse patches.
    Reconstruction at any instant is O(k) patches, aided by an injected
    snapshot cache whose backend determines the eviction policy.
    """

    def __init__(self, snapshots: t.Cache[t.Instant, t.Snapshot]) -> None:
        self._base: t.VarArray | None = None
        self._base_instant: t.Instant | None = None
        self._patches: list[tuple[t.Instant, t.IntArray, t.VarArray]] = []
        self._patch_instants: list[t.Instant] = []
        self.snapshots = snapshots

    def put(self, instant: t.Instant, array: t.VarArray) -> None:
        """Set the full array at instant.

        First call establishes the immutable base.
        Subsequent calls store only the diff as a sparse patch.
        """
        if self._base is None:
            self._base = array.copy()
            self._base.flags.writeable = False
            self._base_instant = instant
            self.snapshots.put(instant, (self._base, -1))
            return

        prev = self._reconstruct(instant)
        changed = array != prev

        if not changed.any():
            return

        idx = numpy.where(changed)[0].astype(numpy.int32)
        vals = array[idx].copy()
        self._insert_patch(instant, idx, vals, full_array=array)

    def put_sparse(self, instant: t.Instant, idx: t.IntArray, vals: t.VarArray) -> None:
        """Store a sparse patch directly without a full N-element array.

        Requires the base to be established via put() first.
        """
        if self._base is None:
            raise ValueError(
                "Cannot call put_sparse before the base is established. "
                "Call put() first for the initial instant."
            )

        if len(idx) == 0:
            return

        self._insert_patch(instant, idx.astype(numpy.int32), vals.copy())

    def get(self, instant: t.Instant) -> t.VarArray | None:
        """Return the reconstructed array as-of instant, or None if not yet set."""
        return self._reconstruct(instant)

    def _insert_patch(
        self,
        instant: t.Instant,
        idx: t.IntArray,
        vals: t.VarArray,
        full_array: t.VarArray | None = None,
    ) -> None:
        pos = bisect.bisect_right(self._patch_instants, instant)
        self._patches.insert(pos, (instant, idx, vals))
        self._patch_instants.insert(pos, instant)
        new_patch_idx = len(self._patches) - 1

        if pos == new_patch_idx:
            if full_array is not None:
                new_snap = full_array.copy()
                new_snap.flags.writeable = False
                self.snapshots.put(instant, (new_snap, new_patch_idx))
            else:
                snap = self._build_snapshot_up_to(instant, new_patch_idx, idx, vals)

                if snap is not None:
                    self.snapshots.put(instant, (snap, new_patch_idx))
        else:
            self.snapshots.evict(lambda k: k >= instant)

    def _build_snapshot_up_to(
        self,
        instant: t.Instant,
        new_patch_idx: int,
        last_idx: t.IntArray,
        last_vals: t.VarArray,
    ) -> t.VarArray | None:
        best_instant = None
        best_array = None
        best_snap_idx = None

        for snap_instant, (snap_array, snap_idx) in self.snapshots.items():
            if snap_instant <= instant:
                if best_instant is None or snap_instant > best_instant:
                    best_instant = snap_instant
                    best_array = snap_array
                    best_snap_idx = snap_idx

        if best_array is None or best_snap_idx is None:
            return None

        new_snap = best_array.copy()

        for i in range(best_snap_idx + 1, new_patch_idx):
            _, pidx, pvals = self._patches[i]
            new_snap[pidx] = pvals

        new_snap[last_idx] = last_vals
        new_snap.flags.writeable = False

        return new_snap

    def _reconstruct(self, instant: t.Instant) -> t.VarArray | None:
        if self._base is None or self._base_instant is None:
            return None

        if instant < self._base_instant:
            return None

        pos = bisect.bisect_right(self._patch_instants, instant)
        last_patch_idx = pos - 1
        cached = self.snapshots.get(instant)

        if cached is not None:
            array, _ = cached
            return array

        best_instant = None
        best_array = None
        best_patch_idx = None

        for snap_instant, (snap_array, snap_idx) in self.snapshots.items():
            if snap_instant < instant:
                if best_instant is None or snap_instant > best_instant:
                    best_instant = snap_instant
                    best_array = snap_array
                    best_patch_idx = snap_idx

        if best_array is not None and best_patch_idx is not None:
            result = best_array

            for i in range(best_patch_idx + 1, last_patch_idx + 1):
                _, idx, vals = self._patches[i]

                if result is best_array:
                    result = result.copy()

                result[idx] = vals

            if result is not best_array:
                result.flags.writeable = False
        elif last_patch_idx == -1:
            result = self._base
        else:
            result = self._base.copy()

            for i in range(last_patch_idx + 1):
                _, idx, vals = self._patches[i]
                result[idx] = vals

            result.flags.writeable = False

        self.snapshots.put(instant, (result, last_patch_idx))

        return result

    def _copy_state_to(self, new: _TemporalStore) -> None:
        new._base = self._base
        new._base_instant = self._base_instant
        new._patches = list(self._patches)
        new._patch_instants = list(self._patch_instants)


class _CounterFactualStore(_TemporalStore):
    """Temporal store with a bounded in-memory snapshot cache.

    The cache class is injectable — use _FIFOCache (default) for
    forward-sequential simulations, _LRUCache for mixed-access patterns.
    """

    def __init__(
        self,
        maxsize: int = 3,
        cache: type = _FIFOCache,
    ) -> None:
        super().__init__(snapshots=cache(maxsize=maxsize))
        self._maxsize = maxsize
        self._cache_class: type = cache

    def clone(self) -> _CounterFactualStore:
        new = _CounterFactualStore(maxsize=self._maxsize, cache=self._cache_class)
        self._copy_state_to(new)
        return new


class _FactualStore(_TemporalStore):
    """Temporal store backed by InMemoryStorage or OnDiskStorage for snapshots.

    Snapshots are kept in the injected storage backend — unbounded by default
    (InMemoryStorage).  Pass an OnDiskStorage to offload snapshot arrays to
    disk under memory pressure.
    """

    def __init__(
        self,
        maxsize: int = 3,
        storage: t.Storage | None = None,
    ) -> None:
        _storage = storage if storage is not None else data_storage.InMemoryStorage()
        super().__init__(snapshots=data_storage.StorageCache(_storage))
        self._maxsize = maxsize
        self._backing_storage = _storage

    def clone(self) -> _FactualStore:
        new = _FactualStore(maxsize=self._maxsize)
        self._copy_state_to(new)
        return new
