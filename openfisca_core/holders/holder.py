from __future__ import annotations

from typing import Any, Optional, Sequence, Union

import os
import warnings

import numpy
import psutil

from openfisca_core import (
    errors,
    commons,
    data_storage as storage,
    indexed_enums as enums,
    periods,
    tools,
    types,
    )

from .memory_usage import MemoryUsage


class Holder:
    """
    A holder keeps tracks of a variable values after they have been calculated, or set as an input.
    """

    def __init__(self, variable, population):
        self.population = population
        self.variable = variable
        self.simulation = population.simulation
        self._memory_storage = storage.InMemoryStorage(is_eternal = (self.variable.definition_period == periods.ETERNITY))

        # By default, do not activate on-disk storage, or variable dropping
        self._disk_storage = None
        self._on_disk_storable = False
        self._do_not_store = False
        if self.simulation and self.simulation.memory_config:
            if self.variable.name not in self.simulation.memory_config.priority_variables:
                self._disk_storage = self.create_disk_storage()
                self._on_disk_storable = True
            if self.variable.name in self.simulation.memory_config.variables_to_drop:
                self._do_not_store = True

    def clone(self, population):
        """
        Copy the holder just enough to be able to run a new simulation without modifying the original simulation.
        """
        new = commons.empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.items():
            if key not in ('population', 'formula', 'simulation'):
                new_dict[key] = value

        new_dict['population'] = population
        new_dict['simulation'] = population.simulation

        return new

    def create_disk_storage(self, directory = None, preserve = False):
        if directory is None:
            directory = self.simulation.data_storage_dir
        storage_dir = os.path.join(directory, self.variable.name)
        if not os.path.isdir(storage_dir):
            os.mkdir(storage_dir)
        return storage.OnDiskStorage(
            storage_dir,
            is_eternal = (self.variable.definition_period == periods.ETERNITY),
            preserve_storage_dir = preserve
            )

    def delete_arrays(self, period = None):
        """
        If ``period`` is ``None``, remove all known values of the variable.

        If ``period`` is not ``None``, only remove all values for any period included in period (e.g. if period is "2017", values for "2017-01", "2017-07", etc. would be removed)
        """

        self._memory_storage.delete(period)
        if self._disk_storage:
            self._disk_storage.delete(period)

    def get_array(self, period):
        """
        Get the value of the variable for the given period.

        If the value is not known, return ``None``.
        """
        if self.variable.is_neutralized:
            return self.default_array()
        value = self._memory_storage.get(period)
        if value is not None:
            return value
        if self._disk_storage:
            return self._disk_storage.get(period)

    def get_memory_usage(self) -> MemoryUsage:
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
            ...     )

            >>> entity = entities.Entity("", "", "", "")

            >>> class MyVariable(variables.Variable):
            ...     definition_period = "year"
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
            nb_cells_by_array = self.population.count,
            dtype = self.variable.dtype,
            )

        usage.update(self._memory_storage.get_memory_usage())

        if self.simulation.trace:
            nb_requests = self.simulation.tracer.get_nb_requests(self.variable.name)
            usage.update(dict(
                nb_requests = nb_requests,
                nb_requests_by_array = nb_requests / float(usage['nb_arrays']) if usage['nb_arrays'] > 0 else numpy.nan
                ))

        return usage

    def get_known_periods(self):
        """
        Get the list of periods the variable value is known for.
        """

        return list(self._memory_storage.get_known_periods()) + list((
            self._disk_storage.get_known_periods() if self._disk_storage else []))

    def set_input(
            self,
            period: types.Period,
            array: Union[numpy.ndarray, Sequence[Any]],
            ) -> Optional[numpy.ndarray]:
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
            ...     definition_period = "year"
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
        if period.unit == periods.ETERNITY and self.variable.definition_period != periods.ETERNITY:
            error_message = os.linesep.join([
                'Unable to set a value for variable {0} for periods.ETERNITY.',
                '{0} is only defined for {1}s. Please adapt your input.',
                ]).format(
                    self.variable.name,
                    self.variable.definition_period
                )
            raise errors.PeriodMismatchError(
                self.variable.name,
                period,
                self.variable.definition_period,
                error_message
                )
        if self.variable.is_neutralized:
            warning_message = "You cannot set a value for the variable {}, as it has been neutralized. The value you provided ({}) will be ignored.".format(self.variable.name, array)
            return warnings.warn(
                warning_message,
                Warning
                )
        if self.variable.value_type in (float, int) and isinstance(array, str):
            array = tools.eval_expression(array)
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
            raise ValueError(
                'Unable to set value "{}" for variable "{}", as its length is {} while there are {} {} in the simulation.'
                .format(value, self.variable.name, len(value), self.population.count, self.population.entity.plural))
        if self.variable.value_type == enums.Enum:
            value = self.variable.possible_values.encode(value)
        if value.dtype != self.variable.dtype:
            try:
                value = value.astype(self.variable.dtype)
            except ValueError:
                raise ValueError(
                    'Unable to set value "{}" for variable "{}", as the variable dtype "{}" does not match the value dtype "{}".'
                    .format(value, self.variable.name, self.variable.dtype, value.dtype))
        return value

    def _set(self, period, value):
        value = self._to_array(value)
        if self.variable.definition_period != periods.ETERNITY:
            if period is None:
                raise ValueError('A period must be specified to set values, except for variables with periods.ETERNITY as as period_definition.')
            if (self.variable.definition_period != period.unit or period.size > 1):
                name = self.variable.name
                period_size_adj = f'{period.unit}' if (period.size == 1) else f'{period.size}-{period.unit}s'
                error_message = os.linesep.join([
                    f'Unable to set a value for variable "{name}" for {period_size_adj}-long period "{period}".',
                    f'"{name}" can only be set for one {self.variable.definition_period} at a time. Please adapt your input.',
                    f'If you are the maintainer of "{name}", you can consider adding it a set_input attribute to enable automatic period casting.'
                    ])

                raise errors.PeriodMismatchError(
                    self.variable.name,
                    period,
                    self.variable.definition_period,
                    error_message
                    )

        should_store_on_disk = (
            self._on_disk_storable and
            self._memory_storage.get(period) is None and  # If there is already a value in memory, replace it and don't put a new value in the disk storage
            psutil.virtual_memory().percent >= self.simulation.memory_config.max_memory_occupation_pc
            )

        if should_store_on_disk:
            self._disk_storage.put(value, period)
        else:
            self._memory_storage.put(value, period)

    def put_in_cache(self, value, period):
        if self._do_not_store:
            return

        if (self.simulation.opt_out_cache and
                self.simulation.tax_benefit_system.cache_blacklist and
                self.variable.name in self.simulation.tax_benefit_system.cache_blacklist):
            return

        self._set(period, value)

    def default_array(self):
        """
        Return a new array of the appropriate length for the entity, filled with the variable default values.
        """

        return self.variable.default_array(self.population.count)
