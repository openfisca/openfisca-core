from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import bisect
import os
import warnings

import numpy
import psutil

from openfisca_core import (
    commons,
    data_storage as storage,
    errors,
    indexed_enums as enums,
    periods,
    types,
)

from . import types as t


class Holder:
    """A holder keeps tracks of a variable values after they have been calculated, or set as an input."""

    def __init__(self, variable, population) -> None:
        self.population = population
        self.variable = variable
        self.simulation = population.simulation
        self._eternal = self.variable.definition_period == periods.DateUnit.ETERNITY
        self._as_of = getattr(self.variable, "as_of", False)
        self._memory_storage = storage.InMemoryStorage(is_eternal=self._eternal)
        if self._as_of:
            # Sparse patch storage.
            # _as_of_base       : first full array set (read-only).
            # _as_of_base_instant: Instant at which the base was established.
            # _as_of_patches    : sorted list of (Instant, idx_array, val_array).
            # _as_of_patch_instants: parallel list of Instants for bisect.
            # _as_of_snapshot   : (Instant, array, last_patch_idx) cursor cache.
            self._as_of_base = None
            self._as_of_base_instant = None
            self._as_of_patches: list = []
            self._as_of_patch_instants: list = []
            self._as_of_snapshot = None
            # Instants for which transition_formula has already been applied.
            self._as_of_transition_computed: set = set()

        # By default, do not activate on-disk storage, or variable dropping
        self._disk_storage = None
        self._on_disk_storable = False
        self._do_not_store = False
        if self.simulation and self.simulation.memory_config:
            if (
                self.variable.name
                not in self.simulation.memory_config.priority_variables
            ):
                self._disk_storage = self.create_disk_storage()
                self._on_disk_storable = True
            if self.variable.name in self.simulation.memory_config.variables_to_drop:
                self._do_not_store = True

    def clone(self, population: t.CorePopulation) -> t.Holder:
        """Copy the holder just enough to be able to run a new simulation without modifying the original simulation."""
        new = commons.empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.items():
            if key not in ("population", "formula", "simulation"):
                new_dict[key] = value

        if self._as_of:
            # _as_of_base is read-only and can be shared between clones.
            # Patch lists must be independent so that writes to the clone
            # don't corrupt the original's list, but the inner arrays (idx/vals)
            # are read-only and can be shared.
            new_dict["_as_of_patches"] = list(self._as_of_patches)
            new_dict["_as_of_patch_instants"] = list(self._as_of_patch_instants)
            # Snapshots are not cloned: first access will reconstruct cheaply.
            new_dict["_as_of_snapshot"] = None
            new_dict["_as_of_transition_computed"] = set(
                self._as_of_transition_computed
            )

        new_dict["population"] = population
        new_dict["simulation"] = population.simulation

        return new

    def create_disk_storage(self, directory=None, preserve=False):
        if directory is None:
            directory = self.simulation.data_storage_dir
        storage_dir = os.path.join(directory, self.variable.name)
        if not os.path.isdir(storage_dir):
            os.mkdir(storage_dir)
        return storage.OnDiskStorage(
            storage_dir,
            self._eternal,
            preserve_storage_dir=preserve,
        )

    def delete_arrays(self, period=None) -> None:
        """If ``period`` is ``None``, remove all known values of the variable.

        If ``period`` is not ``None``, only remove all values for any period included in period (e.g. if period is "2017", values for "2017-01", "2017-07", etc. would be removed)
        """
        self._memory_storage.delete(period)
        if self._disk_storage:
            self._disk_storage.delete(period)

    def get_array(self, period):
        """Get the value of the variable for the given period.

        If the value is not known, return ``None``.
        """
        if self.variable.is_neutralized:
            return self.default_array()
        if self._as_of:
            # Patch-based storage: bypass _memory_storage entirely.
            return self._get_as_of(period)
        value = self._memory_storage.get(period)
        if value is not None:
            return value
        if self._disk_storage:
            return self._disk_storage.get(period)
        return None

    def _get_as_of(self, period):
        """Return the reconstructed array as-of the reference instant of period."""
        target = period.start if self._as_of == "start" else period.stop
        return self._reconstruct_at(target)

    def _reconstruct_at(self, target_instant):
        """Reconstruct the dense array at target_instant from base + patches.

        Uses a snapshot cursor for O(k) incremental cost on forward-sequential
        access patterns.  Falls back to O(N + k*P) full reconstruction for
        backward jumps or first access.

        Returns None if no base has been set yet, or if target_instant is
        before the base was established.
        """
        if self._as_of_base is None or target_instant < self._as_of_base_instant:
            return None

        # Number of patches that apply: all with instant <= target.
        pos = bisect.bisect_right(self._as_of_patch_instants, target_instant)
        last_patch_idx = pos - 1  # -1 means only the base applies

        snapshot = self._as_of_snapshot
        if snapshot is not None:
            snap_instant, snap_array, snap_patch_idx = snapshot

            if snap_instant == target_instant:
                return snap_array  # exact cache hit — O(1)

            if snap_instant < target_instant and snap_patch_idx <= last_patch_idx:
                # Forward access: apply only patches added since the snapshot.
                result = snap_array
                for i in range(snap_patch_idx + 1, last_patch_idx + 1):
                    _, idx, vals = self._as_of_patches[i]
                    if result is snap_array:
                        result = result.copy()
                    result[idx] = vals
                if result is not snap_array:
                    result.flags.writeable = False
                self._as_of_snapshot = (target_instant, result, last_patch_idx)
                return result

        # Full reconstruction from base (backward jump or first access).
        result = self._as_of_base.copy()
        for i in range(last_patch_idx + 1):
            _, idx, vals = self._as_of_patches[i]
            result[idx] = vals
        result.flags.writeable = False
        self._as_of_snapshot = (target_instant, result, last_patch_idx)
        return result

    def _set_as_of(self, period, value) -> None:
        """Store value for an as_of variable using sparse patch storage.

        On the first call: stores the full array as an immutable base.
        On subsequent calls: computes the diff vs the current state at
        period.start and stores only (changed_indices, changed_values) as a
        sparse patch.  If nothing changed, nothing is stored.
        """
        instant = period.start

        if self._as_of_base is None:
            # First set_input: establish the base and seed the snapshot cursor.
            self._as_of_base = value.copy()
            self._as_of_base.flags.writeable = False
            self._as_of_base_instant = instant
            self._as_of_snapshot = (instant, self._as_of_base, -1)
            return

        prev = self._reconstruct_at(instant)
        changed = value != prev
        if not changed.any():
            return  # Value unchanged — no storage needed.

        idx = numpy.where(changed)[0].astype(numpy.int32)
        vals = value[idx].copy()

        # Insert at sorted position (handles out-of-order set_input).
        pos = bisect.bisect_right(self._as_of_patch_instants, instant)
        self._as_of_patches.insert(pos, (instant, idx, vals))
        self._as_of_patch_instants.insert(pos, instant)

        new_patch_idx = len(self._as_of_patches) - 1
        if pos == new_patch_idx:
            # Appended at the end (forward-sequential SET): advance the snapshot
            # to instant so the next GET(instant) is an O(1) cache hit instead
            # of an O(N + M·k) full reconstruction.
            new_snap = value.copy()
            new_snap.flags.writeable = False
            self._as_of_snapshot = (instant, new_snap, new_patch_idx)
        else:
            # Retroactive (out-of-order) SET: invalidate any snapshot that now
            # includes this instant so it is not silently stale.
            if self._as_of_snapshot is not None and self._as_of_snapshot[0] >= instant:
                self._as_of_snapshot = None

    def _set_as_of_sparse(self, period, idx, vals) -> None:
        """Store a sparse patch directly, without requiring a full N-array.

        Bypasses the O(N) diff computation of _set_as_of when the caller
        already knows which elements changed (idx) and their new values (vals).

        idx  : int32 array of changed indices
        vals : array of new values (same dtype as the variable)
        """
        if self._as_of_base is None:
            raise ValueError(
                "Cannot call set_input_sparse before the base is established. "
                "Call set_input first for the initial period."
            )

        instant = period.start

        if len(idx) == 0:
            return  # nothing changed

        # Insert at sorted position (handles out-of-order calls)
        pos = bisect.bisect_right(self._as_of_patch_instants, instant)
        self._as_of_patches.insert(pos, (instant, idx.astype(numpy.int32), vals.copy()))
        self._as_of_patch_instants.insert(pos, instant)

        new_patch_idx = len(self._as_of_patches) - 1
        if pos == new_patch_idx:
            # Forward-sequential: update snapshot from current snapshot + patch
            snapshot = self._as_of_snapshot
            if snapshot is not None:
                snap_instant, snap_array, snap_patch_idx = snapshot
                if snap_instant <= instant:
                    new_snap = (
                        snap_array.copy()
                    )  # O(N) — unavoidable for dense snapshot
                    new_snap[idx] = vals
                    new_snap.flags.writeable = False
                    self._as_of_snapshot = (instant, new_snap, new_patch_idx)
                    return
            # No usable snapshot: leave it None, next GET will rebuild
            if self._as_of_snapshot is not None and self._as_of_snapshot[0] >= instant:
                self._as_of_snapshot = None
        else:
            # Retroactive insert: invalidate stale snapshot
            if self._as_of_snapshot is not None and self._as_of_snapshot[0] >= instant:
                self._as_of_snapshot = None

    def set_input_sparse(self, period, idx, vals) -> None:
        """Set new values for only the specified individuals.

        Unlike set_input(), the caller provides the diff directly:
        - idx  : array of person indices that changed (int)
        - vals : their new values

        This avoids O(N) diff computation when only k << N individuals change.
        Requires that set_input() was called at least once to establish the base.
        """
        if not self._as_of:
            raise ValueError(
                f"set_input_sparse is only valid for as_of variables. "
                f'"{self.variable.name}" does not declare as_of.'
            )
        period = periods.period(period)
        idx = numpy.asarray(idx, dtype=numpy.int32)
        vals = numpy.asarray(vals, dtype=self.variable.dtype)
        self._set_as_of_sparse(period, idx, vals)

    def get_memory_usage(self) -> t.MemoryUsage:
        """Get data about the virtual memory usage of the Holder.

        Returns:
            Memory usage data.

        Examples:
            >>> from pprint import pprint

            >>> from openfisca_core import (
            ...     entities,
            ...     populations,
            ...     simulations,
            ...     taxbenefitsystems,
            ...     variables,
            ... )

            >>> entity = entities.Entity("", "", "", "")

            >>> class MyVariable(variables.Variable):
            ...     definition_period = periods.DateUnit.YEAR
            ...     entity = entity
            ...     value_type = int

            >>> population = populations.Population(entity)
            >>> variable = MyVariable()
            >>> holder = Holder(variable, population)

            >>> tbs = taxbenefitsystems.TaxBenefitSystem([entity])
            >>> entities = {entity.key: population}
            >>> simulation = simulations.Simulation(tbs, entities)
            >>> holder.simulation = simulation

            >>> pprint(holder.get_memory_usage(), indent=3)
            {  'cell_size': nan,
               'dtype': <class 'numpy.int32'>,
               'nb_arrays': 0,
               'nb_cells_by_array': 0,
               'total_nb_bytes': 0...

        """
        usage = t.MemoryUsage(
            nb_cells_by_array=self.population.count,
            dtype=self.variable.dtype,
        )

        usage.update(self._memory_storage.get_memory_usage())

        if self.simulation.trace:
            nb_requests = self.simulation.tracer.get_nb_requests(self.variable.name)
            usage.update(
                {
                    "nb_requests": nb_requests,
                    "nb_requests_by_array": (
                        nb_requests / float(usage["nb_arrays"])
                        if usage["nb_arrays"] > 0
                        else numpy.nan
                    ),
                },
            )

        return usage

    def get_known_periods(self):
        """Get the list of periods the variable value is known for."""
        return list(self._memory_storage.get_known_periods()) + list(
            self._disk_storage.get_known_periods() if self._disk_storage else [],
        )

    def set_input(
        self,
        period: types.Period,
        array: numpy.ndarray | Sequence[Any],
    ) -> numpy.ndarray | None:
        """Set a Variable's array of values of a given Period.

        Args:
            period: The period at which the value is set.
            array: The input value for the variable.

        Returns:
            The set input array.

        Note:
            If a ``set_input`` property has been set for the variable, this
            method may accept inputs for periods not matching the
            ``definition_period`` of the Variable. To read
            more about this, check the `documentation`_.

        Examples:
            >>> from openfisca_core import entities, populations, variables

            >>> entity = entities.Entity("", "", "", "")

            >>> class MyVariable(variables.Variable):
            ...     definition_period = periods.DateUnit.YEAR
            ...     entity = entity
            ...     value_type = float

            >>> variable = MyVariable()

            >>> population = populations.Population(entity)
            >>> population.count = 2

            >>> holder = Holder(variable, population)
            >>> holder.set_input("2018", numpy.array([12.5, 14]))
            >>> holder.get_array("2018")
            array([12.5, 14. ], dtype=float32)

            >>> holder.set_input("2018", [12.5, 14])
            >>> holder.get_array("2018")
            array([12.5, 14. ], dtype=float32)

        .. _documentation:
            https://openfisca.org/doc/coding-the-legislation/35_periods.html#set-input-automatically-process-variable-inputs-defined-for-periods-not-matching-the-definition-period

        """
        period = periods.period(period)

        if period.unit == periods.DateUnit.ETERNITY and not self._eternal:
            error_message = os.linesep.join(
                [
                    "Unable to set a value for variable {1} for {0}.",
                    "{1} is only defined for {2}s. Please adapt your input.",
                ],
            ).format(
                periods.DateUnit.ETERNITY.upper(),
                self.variable.name,
                self.variable.definition_period,
            )
            raise errors.PeriodMismatchError(
                self.variable.name,
                period,
                self.variable.definition_period,
                error_message,
            )
        if self.variable.is_neutralized:
            warning_message = f"You cannot set a value for the variable {self.variable.name}, as it has been neutralized. The value you provided ({array}) will be ignored."
            return warnings.warn(warning_message, Warning, stacklevel=2)
        if self.variable.value_type in (float, int) and isinstance(array, str):
            array = commons.eval_expression(array)
        if self.variable.set_input:
            return self.variable.set_input(self, period, array)
        return self._set(period, array)

    def _to_array(self, value):
        if not isinstance(value, numpy.ndarray):
            value = numpy.asarray(value)
        if value.ndim == 0:
            # 0-dim arrays are casted to scalar when they interact with float. We don't want that.
            value = value.reshape(1)
        if len(value) != self.population.count:
            msg = f'Unable to set value "{value}" for variable "{self.variable.name}", as its length is {len(value)} while there are {self.population.count} {self.population.entity.plural} in the simulation.'
            raise ValueError(
                msg,
            )
        if self.variable.value_type == enums.Enum:
            value = self.variable.possible_values.encode(value)
        if value.dtype != self.variable.dtype:
            try:
                value = value.astype(self.variable.dtype)
            except ValueError:
                msg = f'Unable to set value "{value}" for variable "{self.variable.name}", as the variable dtype "{self.variable.dtype}" does not match the value dtype "{value.dtype}".'
                raise ValueError(
                    msg,
                )
        return value

    def _set(self, period, value) -> None:
        value = self._to_array(value)
        if not self._eternal:
            if period is None:
                msg = (
                    f"A period must be specified to set values, except for variables with "
                    f"{periods.DateUnit.ETERNITY.upper()} as as period_definition."
                )
                raise ValueError(
                    msg,
                )
            if self.variable.definition_period != period.unit or period.size > 1:
                name = self.variable.name
                period_size_adj = (
                    f"{period.unit}"
                    if (period.size == 1)
                    else f"{period.size}-{period.unit}s"
                )
                error_message = os.linesep.join(
                    [
                        f'Unable to set a value for variable "{name}" for {period_size_adj}-long period "{period}".',
                        f'"{name}" can only be set for one {self.variable.definition_period} at a time. Please adapt your input.',
                        f'If you are the maintainer of "{name}", you can consider adding it a set_input attribute to enable automatic period casting.',
                    ],
                )

                raise errors.PeriodMismatchError(
                    self.variable.name,
                    period,
                    self.variable.definition_period,
                    error_message,
                )

        if self._as_of:
            # Sparse patch storage — bypass _memory_storage and disk entirely.
            self._set_as_of(period, value)
            return

        should_store_on_disk = (
            self._on_disk_storable
            and self._memory_storage.get(period) is None
            and psutil.virtual_memory().percent  # If there is already a value in memory, replace it and don't put a new value in the disk storage
            >= self.simulation.memory_config.max_memory_occupation_pc
        )

        if should_store_on_disk:
            self._disk_storage.put(value, period)
        else:
            self._memory_storage.put(value, period)

    def put_in_cache(self, value, period) -> None:
        if self._do_not_store:
            return

        if (
            self.simulation.opt_out_cache
            and self.simulation.tax_benefit_system.cache_blacklist
            and self.variable.name in self.simulation.tax_benefit_system.cache_blacklist
        ):
            return

        self._set(period, value)

    def default_array(self):
        """Return a new array of the appropriate length for the entity, filled with the variable default values."""
        return self.variable.default_array(self.population.count)
