# -*- coding: utf-8 -*-

import logging
import os
import warnings

import numpy as np
import psutil
from typing import TYPE_CHECKING, List, Union, Any, Optional, Dict

from openfisca_core import periods
from openfisca_core.commons import empty_clone
from openfisca_core.data_storage import InMemoryStorage, OnDiskStorage
from openfisca_core.errors import PeriodMismatchError
from openfisca_core.indexed_enums import Enum
from openfisca_core.periods import MONTH, YEAR, ETERNITY, Period
from openfisca_core.tools import eval_expression


if TYPE_CHECKING:
    from openfisca_core.populations import Population
    from openfisca_core.variables import Variable
    from openfisca_core.simulations import Simulation


log = logging.getLogger(__name__)


#TODO change with a more specific type
ArrayLike = Any


class Holder(object):
    """
        A holder keeps tracks of a variable values after they have been calculated, or set as an input.
    """

    def __init__(self, variable:'Variable', population:'Population'):
        self.population:'Population' = population
        self.variable:'Variable' = variable
        # TODO change once decided if simulation is needed or not
        if population.simulation is None:
            raise Exception('You need a simulation attached to the population')
        else:
            self.simulation:'Simulation' = population.simulation
        self._memory_storage:InMemoryStorage = InMemoryStorage(is_eternal = (self.variable.definition_period == ETERNITY))

        # By default, do not activate on-disk storage, or variable dropping
        self._disk_storage:Optional[OnDiskStorage] = None
        self._on_disk_storable:bool = False
        self._do_not_store:bool = False
        if self.simulation and self.simulation.memory_config:
            if self.variable.name not in self.simulation.memory_config.priority_variables:
                self._disk_storage = self.create_disk_storage()
                self._on_disk_storable = True
            if self.variable.name in self.simulation.memory_config.variables_to_drop:
                self._do_not_store = True

    def clone(self, population:'Population')->'Holder':
        """
            Copy the holder just enough to be able to run a new simulation without modifying the original simulation.
        """
        new = empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.items():
            if key not in ('population', 'formula', 'simulation'):
                new_dict[key] = value

        new_dict['population'] = population
        new_dict['simulation'] = population.simulation

        return new

    def create_disk_storage(self, directory:Optional[str] = None, preserve:bool = False)->OnDiskStorage:
        if directory is None:
            directory = self.simulation.data_storage_dir
        storage_dir = os.path.join(directory, self.variable.name)
        if not os.path.isdir(storage_dir):
            os.mkdir(storage_dir)
        return OnDiskStorage(
            storage_dir,
            is_eternal = (self.variable.definition_period == ETERNITY),
            preserve_storage_dir = preserve
            )

    def delete_arrays(self, period:Optional[Union[str, Period]] = None)->None:
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

    def get_memory_usage(self)->Dict[str, Union[int, np.dtype]]:
        """
            Get data about the virtual memory usage of the holder.

            :returns: Memory usage data
            :rtype: dict

            Example:

            >>> holder.get_memory_usage()
            >>> {
            >>>    'nb_arrays': 12,  # The holder contains the variable values for 12 different periods
            >>>    'nb_cells_by_array': 100, # There are 100 entities (e.g. persons) in our simulation
            >>>    'cell_size': 8,  # Each value takes 8B of memory
            >>>    'dtype': dtype('float64')  # Each value is a float 64
            >>>    'total_nb_bytes': 10400  # The holder uses 10.4kB of virtual memory
            >>>    'nb_requests': 24  # The variable has been computed 24 times
            >>>    'nb_requests_by_array': 2  # Each array stored has been on average requested twice
            >>>    }
        """

        usage = dict(
            nb_cells_by_array = self.population.count,
            dtype = self.variable.dtype,
            )

        usage.update(self._memory_storage.get_memory_usage())

        if self.simulation.trace:
            nb_requests = self.simulation.tracer.get_nb_requests(self.variable.name)
            usage.update(dict(
                nb_requests = nb_requests,
                nb_requests_by_array = nb_requests / float(usage['nb_arrays']) if usage['nb_arrays'] > 0 else np.nan
                ))

        return usage

    def get_known_periods(self)->List[Period]:
        """
            Get the list of periods the variable value is known for.
        """

        return list(self._memory_storage.get_known_periods()) + list((
            self._disk_storage.get_known_periods() if self._disk_storage else []))

    def set_input(self, period:Union[str, Period], array: ArrayLike):
        """
            Set a variable's value (``array``) for a given period (``period``)

            :param array: the input value for the variable
            :param period: the period at which the value is setted

            Example :

            >>> holder.set_input([12, 14], '2018-04')
            >>> holder.get_array('2018-04')
            >>> [12, 14]


            If a ``set_input`` property has been set for the variable, this method may accept inputs for periods not matching the ``definition_period`` of the variable. To read more about this, check the `documentation <https://openfisca.org/doc/coding-the-legislation/35_periods.html#set-input-automatically-process-variable-inputs-defined-for-periods-not-matching-the-definition-period>`_.
        """

        period = periods.period(period)
        if period.unit == ETERNITY and self.variable.definition_period != ETERNITY:
            error_message = os.linesep.join([
                'Unable to set a value for variable {0} for ETERNITY.',
                '{0} is only defined for {1}s. Please adapt your input.',
                ]).format(
                    self.variable.name,
                    self.variable.definition_period
                )
            raise PeriodMismatchError(
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
            array = eval_expression(array)
        if self.variable.set_input:
            return self.variable.set_input(self, period, array)
        return self._set(period, array)

    def _to_array(self, value:ArrayLike)->np.array:
        if not isinstance(value, np.ndarray):
            value = np.asarray(value)
        if value.ndim == 0:
            # 0-dim arrays are casted to scalar when they interact with float. We don't want that.
            value = value.reshape(1)
        if len(value) != self.population.count:
            raise ValueError(
                'Unable to set value "{}" for variable "{}", as its length is {} while there are {} {} in the simulation.'
                .format(value, self.variable.name, len(value), self.population.count, self.population.entity.plural))
        if self.variable.value_type == Enum:
            value = self.variable.possible_values.encode(value)
        if value.dtype != self.variable.dtype:
            try:
                value = value.astype(self.variable.dtype)
            except ValueError:
                raise ValueError(
                    'Unable to set value "{}" for variable "{}", as the variable dtype "{}" does not match the value dtype "{}".'
                    .format(value, self.variable.name, self.variable.dtype, value.dtype))
        return value

    def _set(self, period:Union[Period, None], value:ArrayLike)->None:
        value = self._to_array(value)
        if self.variable.definition_period != ETERNITY:
            if period is None:
                raise ValueError('A period must be specified to set values, except for variables with ETERNITY as as period_definition.')
            if (self.variable.definition_period != period.unit or period.size > 1):
                name = self.variable.name
                period_size_adj = f'{period.unit}' if (period.size == 1) else f'{period.size}-{period.unit}s'
                error_message = os.linesep.join([
                    f'Unable to set a value for variable "{name}" for {period_size_adj}-long period "{period}".',
                    f'"{name}" can only be set for one {self.variable.definition_period} at a time. Please adapt your input.',
                    f'If you are the maintainer of "{name}", you can consider adding it a set_input attribute to enable automatic period casting.'
                    ])

                raise PeriodMismatchError(
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

    def put_in_cache(self, value:ArrayLike, period:Period)->None:
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


def set_input_dispatch_by_period(holder:'Holder', period:Period, array):
    """
        This function can be declared as a ``set_input`` attribute of a variable.

        In this case, the variable will accept inputs on larger periods that its definition period, and the value for the larger period will be applied to all its subperiods.

        To read more about ``set_input`` attributes, check the `documentation <https://openfisca.org/doc/coding-the-legislation/35_periods.html#set-input-automatically-process-variable-inputs-defined-for-periods-not-matching-the-definition-period>`_.
    """
    array = holder._to_array(array)

    period_size = period.size
    period_unit = period.unit

    if holder.variable.definition_period == MONTH:
        cached_period_unit = periods.MONTH
    elif holder.variable.definition_period == YEAR:
        cached_period_unit = periods.YEAR
    else:
        raise ValueError('set_input_dispatch_by_period can be used only for yearly or monthly variables.')

    after_instant = period.start.offset(period_size, period_unit)

    # Cache the input data, skipping the existing cached months
    sub_period = period.start.period(cached_period_unit)
    while sub_period.start < after_instant:
        existing_array = holder.get_array(sub_period)
        if existing_array is None:
            holder._set(sub_period, array)
        else:
            # The array of the current sub-period is reused for the next ones.
            # TODO: refactor or document this behavior
            array = existing_array
        sub_period = sub_period.offset(1)


def set_input_divide_by_period(holder:Holder, period:Period, array)->None:
    """
        This function can be declared as a ``set_input`` attribute of a variable.

        In this case, the variable will accept inputs on larger periods that its definition period, and the value for the larger period will be divided between its subperiods.

        To read more about ``set_input`` attributes, check the `documentation <https://openfisca.org/doc/coding-the-legislation/35_periods.html#set-input-automatically-process-variable-inputs-defined-for-periods-not-matching-the-definition-period>`_.
    """
    if not isinstance(array, np.ndarray):
        array = np.array(array)
    period_size = period.size
    period_unit = period.unit

    if holder.variable.definition_period == MONTH:
        cached_period_unit = periods.MONTH
    elif holder.variable.definition_period == YEAR:
        cached_period_unit = periods.YEAR
    else:
        raise ValueError('set_input_divide_by_period can be used only for yearly or monthly variables.')

    after_instant = period.start.offset(period_size, period_unit)

    # Count the number of elementary periods to change, and the difference with what is already known.
    remaining_array = array.copy()
    sub_period = period.start.period(cached_period_unit)
    sub_periods_count = 0
    while sub_period.start < after_instant:
        existing_array = holder.get_array(sub_period)
        if existing_array is not None:
            remaining_array -= existing_array
        else:
            sub_periods_count += 1
        sub_period = sub_period.offset(1)

    # Cache the input data
    if sub_periods_count > 0:
        divided_array = remaining_array / sub_periods_count
        sub_period = period.start.period(cached_period_unit)
        while sub_period.start < after_instant:
            if holder.get_array(sub_period) is None:
                holder._set(sub_period, divided_array)
            sub_period = sub_period.offset(1)
    elif not (remaining_array == 0).all():
        raise ValueError("Inconsistent input: variable {0} has already been set for all months contained in period {1}, and value {2} provided for {1} doesn't match the total ({3}). This error may also be thrown if you try to call set_input twice for the same variable and period.".format(holder.variable.name, period, array, array - remaining_array))
