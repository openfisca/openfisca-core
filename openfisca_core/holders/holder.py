from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from typing_extensions import Literal

from openfisca_core.types import Period, Population, Simulation, Variable

import itertools
import os
import warnings

import numpy
import psutil
from sortedcontainers import sorteddict

from openfisca_core import (
    commons,
    errors,
    experimental,
    indexed_enums as enums,
    periods,
    tools,
)

from .repos import DiskRepo, MemoryRepo
from .typing import MemoryUsage, Storage


class Holder:
    """Caches calculated or input variable values."""

    variable: Variable
    population: Population
    simulation: Simulation
    __stores__: dict[Literal["memory", "disk"], Storage]

    def __init__(self, variable: Variable, population: Population) -> None:
        self.variable = variable
        self.population = population
        self.simulation = population.simulation

        if self.storable:
            self.stores = sorteddict.SortedDict(
                {
                    "memory": MemoryRepo(),
                    "disk": self.create_disk_repo(),
                }
            )

        else:
            self.stores = sorteddict.SortedDict(
                {
                    "memory": MemoryRepo(),
                }
            )

    @property
    def name(self) -> str:
        return self.variable.name

    @property
    def period(self) -> Period:
        return self.variable.definition_period

    @property
    def eternal(self) -> bool:
        return self.period == periods.DateUnit.ETERNITY

    @property
    def neutralised(self) -> bool:
        return self.variable.is_neutralized

    @property
    def config(self) -> experimental.MemoryConfig | None:
        try:
            return self.simulation.memory_config

        except AttributeError:
            return None

    @property
    def durable(self) -> bool:
        return bool(self.config)

    @property
    def transient(self) -> bool:
        return not self.durable

    @property
    def storable(self) -> bool:
        if self.transient:
            return False

        if self.config is None:
            return False

        return self.name not in self.config.priority_variables

    @property
    def cacheable(self) -> bool:
        if self.transient:
            return False

        if self.config is None:
            return False

        return self.name not in self.config.variables_to_drop

    @property
    def stores(self) -> dict[Literal["memory", "disk"], Storage]:
        return self.__stores__

    @stores.setter
    def stores(self, stores: dict[Literal["memory", "disk"], Storage]) -> None:
        self.__stores__ = stores

    def clone(self, population):
        """
        Copies the holder just enough to be able to run a new simulation without modifying the original simulation.
        """
        new = commons.empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.items():
            if key not in ("population", "formula", "simulation"):
                new_dict[key] = value

        new_dict["population"] = population
        new_dict["simulation"] = population.simulation

        return new

    def create_disk_repo(
        self,
        directory: str | None = None,
        preserve: bool = False,
    ) -> Storage:
        if directory is None:
            directory = self.simulation.data_storage_dir

        storage_dir = os.path.join(directory, self.name)

        if not os.path.isdir(storage_dir):
            os.mkdir(storage_dir)

        return DiskRepo(storage_dir, preserve)

    def delete_arrays(self, period: Any = None) -> None:
        """
        If ``period`` is ``None``, remove all known values of the variable.

        If ``period`` is not ``None``, only remove all values for any period included in period (e.g. if period is "2017", values for "2017-01", "2017-07", etc. would be removed)
        """

        if self.eternal and period is not None:
            period = periods.period(periods.DateUnit.ETERNITY)

        else:
            period = periods.period(period)

        for store in self.stores.values():
            store.delete(period)

        return None

    def get_array(self, period: Period) -> numpy.ndarray | None:
        """
        Gets the value of the variable for the given period.

        If the value is not known, return ``None``.
        """
        if self.neutralised:
            return self.variable.default_array(self.population.count)

        if self.eternal:
            period = periods.period(periods.DateUnit.ETERNITY)

        else:
            period = periods.period(period)

        for store in self.stores.values():
            value = store.get(period)

            if value is not None:
                return value

        return None

    def get_memory_usage(self) -> MemoryUsage:
        """Gets data about the virtual memory usage of the Holder.

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
            ...     )

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

            >>> pprint(holder.get_memory_usage(), indent = 3)
            {  'cell_size': nan,
               'dtype': <class 'numpy.int32'>,
               'nb_arrays': 0,
               'nb_cells_by_array': 0,
               'total_nb_bytes': 0...

        """

        usage = MemoryUsage(
            nb_cells_by_array=self.population.count,
            dtype=self.variable.dtype,
        )

        usage.update(self.stores["memory"].usage())

        if self.simulation.trace:
            nb_requests = self.simulation.tracer.get_nb_requests(self.name)
            usage.update(
                dict(
                    nb_requests=nb_requests,
                    nb_requests_by_array=(
                        nb_requests / float(usage["nb_arrays"])
                        if usage["nb_arrays"] > 0
                        else numpy.nan
                    ),
                )
            )

        return usage

    def get_known_periods(self) -> Sequence[Period]:
        """
        Gets the list of periods the variable value is known for.
        """

        known_periods = (store.periods() for store in self.stores.values())

        return list(itertools.chain(*known_periods))

    def set_input(
        self,
        period: Period,
        array: numpy.ndarray | Sequence[Any],
    ) -> numpy.ndarray | None:
        """Sets a Variable's array of values of a given Period.

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
            ...     value_type = int

            >>> variable = MyVariable()

            >>> population = populations.Population(entity)
            >>> population.count = 2

            >>> holder = Holder(variable, population)
            >>> holder.set_input("2018", numpy.array([12.5, 14]))
            >>> holder.get_array("2018")
            array([12, 14], dtype=int32)

            >>> holder.set_input("2018", [12.5, 14])
            >>> holder.get_array("2018")
            array([12, 14], dtype=int32)

        .. _documentation:
            https://openfisca.org/doc/coding-the-legislation/35_periods.html#set-input-automatically-process-variable-inputs-defined-for-periods-not-matching-the-definition-period

        """

        period = periods.period(period)

        if period.unit == periods.DateUnit.ETERNITY and not self.eternal:
            error_message = os.linesep.join(
                [
                    f"Unable to set a value for variable {self.name} for {periods.DateUnit.ETERNITY.upper()}.",
                    f"{self.name} is only defined for {self.period}s. Please adapt your input.",
                ]
            )

            raise errors.PeriodMismatchError(
                self.name, period, self.period, error_message
            )

        if self.neutralised:
            warning_message = f"You cannot set a value for the variable {self.name}, as it has been neutralized. The value you provided ({array}) will be ignored."
            return warnings.warn(
                warning_message,
                Warning,
                stacklevel=2,
            )

        if self.variable.value_type in (float, int) and isinstance(array, str):
            array = tools.eval_expression(array)

        if self.variable.set_input:
            return self.variable.set_input(self, period, array)

        self._set(period, array)

        return None

    def _to_array(self, value: Any) -> numpy.ndarray:
        if not isinstance(value, numpy.ndarray):
            value = numpy.asarray(value)

        if value.ndim == 0:
            # 0-dim arrays are casted to scalar when they interact with float. We don't want that.
            value = value.reshape(1)

        if len(value) != self.population.count:
            raise ValueError(
                'Unable to set value "{}" for variable "{}", as its length is {} while there are {} {} in the simulation.'.format(
                    value,
                    self.name,
                    len(value),
                    self.population.count,
                    self.population.entity.plural,
                )
            )

        if self.variable.value_type == enums.Enum:
            value = self.variable.possible_values.encode(value)

        if value.dtype != self.variable.dtype:
            try:
                value = value.astype(self.variable.dtype)

            except ValueError:
                raise ValueError(
                    'Unable to set value "{}" for variable "{}", as the variable dtype "{}" does not match the value dtype "{}".'.format(
                        value, self.name, self.variable.dtype, value.dtype
                    )
                )

        return value

    def _set(self, period: Period | None, value: numpy.ndarray | Sequence[Any]) -> None:
        value = self._to_array(value)

        if self.eternal:
            period = periods.period(periods.DateUnit.ETERNITY)

        else:
            if period is None:
                raise ValueError(
                    f"A period must be specified to set values, except for variables with "
                    f"{periods.DateUnit.ETERNITY.upper()} as as period_definition."
                )

            if self.period != period.unit or period.size > 1:
                name = self.name
                period_size_adj = (
                    f"{period.unit}"
                    if (period.size == 1)
                    else f"{period.size}-{period.unit}s"
                )
                error_message = os.linesep.join(
                    [
                        f'Unable to set a value for variable "{name}" for {period_size_adj}-long period "{period}".',
                        f'"{name}" can only be set for one {self.period} at a time. Please adapt your input.',
                        f'If you are the maintainer of "{name}", you can consider adding it a set_input attribute to enable automatic period casting.',
                    ]
                )

                raise errors.PeriodMismatchError(
                    self.name, period, self.period, error_message
                )

        should_store_on_disk = (
            self.storable
            and self.stores["memory"].get(period) is None
            and psutil.virtual_memory().percent
            # If there is already a value in memory, replace it
            # and don't put a new value in the disk storage
            >= self.simulation.memory_config.max_memory_occupation_pc
        )

        if should_store_on_disk:
            self.stores["disk"].put(value, period)

        else:
            self.stores["memory"].put(value, period)

    def put_in_cache(self, value: numpy.ndarray, period: Period) -> None:
        if not self.transient and not self.cacheable:
            return None

        if (
            self.simulation.opt_out_cache
            and self.simulation.tax_benefit_system.cache_blacklist
            and self.name in self.simulation.tax_benefit_system.cache_blacklist
        ):
            return

        self._set(period, value)
