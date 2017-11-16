# -*- coding: utf-8 -*-


from __future__ import division
import warnings
import os

import numpy as np

from . import periods
from .commons import empty_clone
from .periods import MONTH, YEAR, ETERNITY
from columns import make_column_from_variable
from indexed_enums import Enum, EnumArray
import logging

log = logging.getLogger(__name__)

class DatedHolder(object):
    """
        A wrapper of the value of a variable for a given period (and possibly a given set of extra parameters).
    """
    holder = None
    period = None
    extra_params = None

    def __init__(self, holder, period, value, extra_params = None):
        self.holder = holder
        self.period = period
        self.extra_params = extra_params
        self.value = value

    @property
    def array(self):
        return self.value

    @array.setter
    def array(self, array):
        raise ValueError('Impossible to modify DatedHolder.array. Please use Holder.put_in_cache.')

    @property
    def variable(self):
        return self.holder.variable

    @property
    def entity(self):
        return self.holder.entity

    def to_value_json(self, use_label = False):
        column = make_column_from_variable(self.holder.variable)
        transform_dated_value_to_json = column.transform_dated_value_to_json
        return [
            transform_dated_value_to_json(cell, use_label = use_label)
            for cell in self.array.tolist()
            ]


class Holder(object):
    """
        A holder keeps tracks of a variable values after they have been calculated, or set as an input.
    """
    _array = None  # Only used when variable.definition_period == ETERNITY
    _array_by_period = None  # Only used when variable.definition_period != ETERNITY
    variable = None
    entity = None
    formula = None
    formula_output_period_by_requested_period = None

    def __init__(self, simulation = None, variable = None, entity = None):
        assert variable is not None
        assert self.variable is None
        if simulation is not None:
            warnings.warn(
                u"The Holder(simulation, variable) constructor has been deprecated. "
                u"Please use Holder(entity = entity, variable = variable) instead.",
                Warning
                )
            self.simulation = simulation
            self.entity = simulation.get_entity(variable.entity)
        else:
            self.entity = entity
            self.simulation = entity.simulation
        self.variable = variable
        self.buffer = {}
        self._data_store_dir = None

    @property
    def array(self):
        if self.variable.definition_period != ETERNITY:
            return self.get_array(self.simulation.period)
        return self._array

    @array.setter
    def array(self, array):
        if self.variable.definition_period != ETERNITY:
            return self.put_in_cache(array, self.simulation.period)
        self._array = array

    def calculate(self, period, **parameters):
        dated_holder = self.compute(period = period, **parameters)
        return dated_holder.array

    def calculate_output(self, period):
        return self.formula.calculate_output(period)

    def clone(self, entity):
        """Copy the holder just enough to be able to run a new simulation without modifying the original simulation."""
        new = empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.iteritems():
            if key in ('_array_by_period',):
                if value is not None:
                    # There is no need to copy the arrays, because the formulas don't modify them.
                    new_dict[key] = value.copy()
            elif key not in ('entity', 'formula', 'simulation'):
                new_dict[key] = value

        new_dict['entity'] = entity
        new_dict['simulation'] = entity.simulation
        # Caution: formula must be cloned after the entity has been set into new.
        formula = self.formula
        if formula is not None:
            new_dict['formula'] = formula.clone(new)

        return new

    def compute(self, period, **parameters):
        """
            Compute the variable's value for the ``period`` and return a dated holder containing the value.
        """

        if self.simulation.trace:
            self.simulation.tracer.record_calculation_start(self.variable.name, period, **parameters)
        variable = self.variable

        # Check that the requested period matches definition_period
        if variable.definition_period != ETERNITY:
            if variable.definition_period == MONTH and period.unit != periods.MONTH:
                raise ValueError(u'Unable to compute variable {0} for period {1} : {0} must be computed for a whole month. You can use the ADD option to sum {0} over the requested period, or change the requested period to "period.first_month".'.format(
                    variable.name,
                    period
                    ).encode('utf-8'))
            if variable.definition_period == YEAR and period.unit != periods.YEAR:
                raise ValueError(u'Unable to compute variable {0} for period {1} : {0} must be computed for a whole year. You can use the DIVIDE option to get an estimate of {0} by dividing the yearly value by 12, or change the requested period to "period.this_year".'.format(
                    variable.name,
                    period
                    ).encode('utf-8'))
            if period.size != 1:
                raise ValueError(u'Unable to compute variable {0} for period {1} : {0} must be computed for a whole {2}. You can use the ADD option to sum {0} over the requested period.'.format(
                    variable.name,
                    period,
                    'month' if variable.definition_period == MONTH else 'year').encode('utf-8'))

        extra_params = parameters.get('extra_params')

        # First look for a value already cached
        holder_or_dated_holder = self.get_from_cache(period, extra_params)
        if holder_or_dated_holder.array is not None:
            if self.simulation.trace:
                self.simulation.tracer.record_calculation_end(self.variable.name, period, holder_or_dated_holder.array, **parameters)
            return holder_or_dated_holder
        assert self._array is None  # self._array should always be None when dated_holder.array is None.

        # Request a computation
        dated_holder = self.formula.compute(period = period, **parameters)
        formula_dated_holder = self.put_in_cache(dated_holder.array, period, extra_params)
        if self.simulation.trace:
            self.simulation.tracer.record_calculation_end(self.variable.name, period, dated_holder.array, **parameters)
        return formula_dated_holder

    def compute_add(self, period, **parameters):
        # Check that the requested period matches definition_period
        if self.variable.definition_period == YEAR and period.unit == periods.MONTH:
            raise ValueError(u'Unable to compute variable {0} for period {1} : {0} can only be computed for year-long periods. You can use the DIVIDE option to get an estimate of {0} by dividing the yearly value by 12, or change the requested period to "period.this_year".'.format(
                self.variable.name,
                period,
                ).encode('utf-8'))

        if self.variable.definition_period == MONTH:
            variable_definition_period = periods.MONTH
        elif self.variable.definition_period == YEAR:
            variable_definition_period = periods.YEAR
        else:
            raise ValueError(u'Unable to sum constant variable {} over period {} : only variables defined monthly or yearly can be summed over time.'.format(
                self.variable.name,
                period).encode('utf-8'))

        after_instant = period.start.offset(period.size, period.unit)
        sub_period = period.start.period(variable_definition_period)
        array = None
        while sub_period.start < after_instant:
            dated_holder = self.compute(period = sub_period, **parameters)
            if array is None:
                array = dated_holder.array.copy()
            else:
                array += dated_holder.array
            sub_period = sub_period.offset(1)

        return DatedHolder(self, period, array, parameters.get('extra_params'))

    def compute_divide(self, period, **parameters):
        # Check that the requested period matches definition_period
        if self.variable.definition_period != YEAR:
            raise ValueError(u'Unable to divide the value of {} over time (on period {}) : only variables defined yearly can be divided over time.'.format(
                self.variable.name,
                period).encode('utf-8'))

        if period.size != 1:
            raise ValueError("DIVIDE option can only be used for a one-year or a one-month requested period")

        if period.unit == periods.MONTH:
            computation_period = period.this_year
            dated_holder = self.compute(period = computation_period, **parameters)
            array = dated_holder.array / 12.
            return DatedHolder(self, period, array, parameters.get('extra_params'))
        elif period.unit == periods.YEAR:
            return self.compute(period, **parameters)

        raise ValueError(u'Unable to divide the value of {} to match the period {}.'.format(
            self.variable.name,
            period).encode('utf-8'))

    def delete_arrays(self, period = None):
        """
            If ``period`` is ``None``, remove all known values of the variable.

            If ``period`` is not ``None``, only remove all values for any period included in period (e.g. if period is "2017", values for "2017-01", "2017-07", etc. would be removed)

        """
        if self._array is not None:
            del self._array
        if self._array_by_period is not None and period is None:
            del self._array_by_period
        if period is not None:
            if not isinstance(period, periods.Period):
                period = periods.period(period)
            self._array_by_period = {
                period_item: value
                for period_item, value in self._array_by_period.iteritems()
                if not period.contains(period_item)
                }

    def get_array(self, period, extra_params = None):
        if self.variable.definition_period == ETERNITY:
            return self.array
        assert period is not None
        array_by_period = self._array_by_period
        if array_by_period is not None:
            values = array_by_period.get(period)
            if values is not None:
                if extra_params:
                    return values.get(tuple(extra_params))
                else:
                    if(type(values) == dict):
                        return values.values()[0]
                    return values
        return None

    def graph(self, edges, get_input_variables_and_parameters, nodes, visited):
        variable = self.variable
        if self in visited:
            return
        visited.add(self)
        nodes.append(dict(
            id = variable.name,
            group = self.entity.key,
            label = variable.name,
            title = variable.label,
            ))
        formula = self.formula
        if formula is None:
            return
        formula.graph_parameters(edges, get_input_variables_and_parameters, nodes, visited)

    def get_memory_usage(self):
        """
            Gets data about the virtual memory usage of the holder.

            :returns: Memory usage data
            :rtype: dict

            Exemple:

            >>> holder.get_memory_usage()
            >>> {
            >>>    'nb_arrays': 12,  # The holder contains the variable values for 12 different periods
            >>>    'nb_cells_by_array': 100, # There are 100 entities (e.g. persons) in our simulation
            >>>    'cell_size': 8,  # Each value takes 8B of memory
            >>>    'dtype': dtype('float64')  # Each value is a float 64
            >>>    'total_nb_bytes': 10400  # The holder uses 10.4kB of virtual memory
            >>>    }
        """

        usage = dict(
            nb_cells_by_array = self.entity.count,
            dtype = self.variable.dtype,
            )

        if self._array is not None:
            # self._array is only used when definition period is ETERNITY"
            usage.update(dict(
                nb_arrays = 1,
                total_nb_bytes = self._array.nbytes,
                cell_size = self._array.itemsize,
                ))
            return usage
        elif self._array_by_period is not None:
            nb_arrays = sum([
                len(array_or_dict) if isinstance(array_or_dict, dict) else 1
                for array_or_dict in self._array_by_period.itervalues()
                ])
            array = self._array_by_period.values()[0]
            if isinstance(array, dict):
                array = array.values()[0]
            usage.update(dict(
                nb_arrays = nb_arrays,
                total_nb_bytes = array.nbytes * nb_arrays,
                cell_size = array.itemsize,
                ))
            return usage
        else:
            usage.update(dict(
                nb_arrays = 0,
                total_nb_bytes = 0,
                cell_size = np.nan,
                ))
            return usage

    def get_known_periods(self):
        """
        Get the list of periods the variable value is known for.
        """
        if self.variable.definition_period == ETERNITY:
            if self.array is not None:
                return [ETERNITY]
            else:
                return []
        return self._array_by_period.keys()

    @property
    def real_formula(self):
        formula = self.formula
        if formula is None:
            return None
        return formula.real_formula

    def set_input(self, period, array):
        if period.unit == ETERNITY and self.variable.definition_period != ETERNITY:
            error_message = os.linesep.join([
                u'Unable to set a value for variable {0} for ETERNITY.',
                u'{0} is only defined for {1}s. Please adapt your input.',
                ]).format(
                    self.variable.name,
                    self.variable.definition_period
                ).encode('utf-8')
            raise PeriodMismatchError(
                self.variable.name,
                period,
                self.variable.definition_period,
                error_message
                )

        self.formula.set_input(period, array)

    @property
    def data_store_dir(self):
        """
        Temporary folder used to store intermediate calculation data in case the memory is saturated
        """
        if self._data_store_dir is None:
            self._data_store_dir = os.path.join(self.simulation.data_store_dir, self.variable.name)
            os.makedirs(self._data_store_dir)
        return self._data_store_dir

    def put_in_disk_cache(self, value, period, extra_params = None):
        filename = (ETERNITY if self.variable.definition_period == ETERNITY else str(period))
        if extra_params:
            filename = '{}_{}'.format(filename, '_'.join([str(param) for param in extra_params]))
        path = os.path.join(self.data_store_dir, filename) + '.npy'
        np.save(path, value)
        return DatedHolder(self, period, value, extra_params)

    def put_in_cache(self, value, period, extra_params = None):
        simulation = self.simulation

        if self.variable.value_type == Enum:
            value = self.variable.possible_values.encode(value)

        if value.dtype != self.variable.dtype:
            try:
                value = value.astype(self.variable.dtype)
            except ValueError:
                raise ValueError(
                    u'Unable to set value "{}" for variable "{}", as the variable dtype "{}" does not match the value dtype "{}".'
                    .format(value, self.variable.name, self.variable.dtype, value.dtype)
                    .encode('utf-8'))

        if self.variable.definition_period != ETERNITY:
            if period is None:
                raise ValueError('A period must be specified to put values in cache, except for variables with ETERNITY as as period_definition.')
            if ((self.variable.definition_period == MONTH and period.unit != periods.MONTH) or
               (self.variable.definition_period == YEAR and period.unit != periods.YEAR)):
                error_message = os.linesep.join([
                    u'Unable to set a value for variable {0} for {1}-long period {2}.',
                    u'{0} is only defined for {3}s. Please adapt your input.',
                    u'If you are the maintainer of {0}, you can consider adding it a set_input attribute to enable automatic period casting.'
                    ]).format(
                        self.variable.name,
                        period.unit,
                        period,
                        self.variable.definition_period
                    ).encode('utf-8')

                raise PeriodMismatchError(
                    self.variable.name,
                    period,
                    self.variable.definition_period,
                    error_message
                    )

        if (simulation.opt_out_cache and
                simulation.tax_benefit_system.cache_blacklist and
                self.variable.name in simulation.tax_benefit_system.cache_blacklist):
            return DatedHolder(self, period, value, extra_params)

        return self.put_in_disk_cache(value, period, extra_params)

    def put_in_memory_cache(self, value, period, extra_params = None):

        if self.variable.definition_period == ETERNITY:
            self.array = value
        array_by_period = self._array_by_period
        if array_by_period is None:
            self._array_by_period = array_by_period = {}
        if extra_params is None:
            array_by_period[period] = value
        else:
            if array_by_period.get(period) is None:
                array_by_period[period] = {}
            array_by_period[period][tuple(extra_params)] = value
        return self.get_from_cache(period, extra_params)

    def get_from_memory_cache(self, period, extra_params = None):
        if self.variable.definition_period == ETERNITY:
            return self

        value = self.get_array(period, extra_params)
        return DatedHolder(self, period, value, extra_params)

    def get_from_disk_cache(self, period, extra_params = None):
        filename = ETERNITY if self.variable.definition_period == ETERNITY else str(period)
        if extra_params:
            filename = '{}_{}'.format(filename, '_'.join([str(param) for param in extra_params]))
        path = os.path.join(self.data_store_dir, filename) + '.npy'
        value = None
        if os.path.isfile(path):
            value = np.load(path)
        return DatedHolder(self, period, value, extra_params)

    def get_from_cache(self, period, extra_params = None):
        if self.variable.is_neutralized:
            return DatedHolder(self, period, value = self.default_array())

        return self.get_from_disk_cache(period, extra_params)

    def get_extra_param_names(self, period):
        function = self.formula.find_function(period)

        return function.__func__.func_code.co_varnames[3:]

    def to_value_json(self, use_label = False):
        column = make_column_from_variable(self.variable)
        transform_dated_value_to_json = column.transform_dated_value_to_json

        def extra_params_to_json_key(extra_params, period):
            return '{' + ', '.join(
                ['{}: {}'.format(name, value)
                    for name, value in zip(self.get_extra_param_names(period), extra_params)]
                ) + '}'

        if self.variable.definition_period == ETERNITY:
            array = self._array
            if array is None:
                return None
            return [
                transform_dated_value_to_json(cell, use_label = use_label)
                for cell in array.tolist()
                ]
        value_json = {}
        if self._array_by_period is not None:
            for period, array_or_dict in self._array_by_period.iteritems():
                if type(array_or_dict) == dict:
                    value_json[str(period)] = values_dict = {}
                    for extra_params, array in array_or_dict.iteritems():
                        extra_params_key = extra_params_to_json_key(extra_params, period)
                        values_dict[str(extra_params_key)] = [
                            transform_dated_value_to_json(cell, use_label = use_label)
                            for cell in array.tolist()
                            ]
                else:
                    value_json[str(period)] = [
                        transform_dated_value_to_json(cell, use_label = use_label)
                        for cell in array_or_dict.tolist()
                        ]
        return value_json

    def default_array(self):
        array_size = self.entity.count
        array = np.empty(array_size, dtype = self.variable.dtype)
        if self.variable.value_type == Enum:
            array.fill(self.variable.default_value.index)
            return EnumArray(array, self.variable.possible_values)
        array.fill(self.variable.default_value)
        return array


class PeriodMismatchError(ValueError):
    def __init__(self, variable_name, period, definition_period, message):
        self.variable_name = variable_name
        self.period = period
        self.definition_period = definition_period
        ValueError.__init__(self, message)
