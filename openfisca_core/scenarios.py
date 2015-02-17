# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import division

import collections

import numpy as np

from . import conv, periods, simulations


N_ = lambda message: message


class AbstractScenario(object):
    axes = None
    period = None
    tax_benefit_system = None
    test_case = None

    @staticmethod
    def cleanup_period_in_json_or_python(value, state = None):
        if value is None:
            return None, None
        value = value.copy()
        if 'date' not in value:
            year = value.pop('year', None)
            if year is not None:
                value['date'] = year
        if 'period' not in value:
            date = value.pop('date', None)
            if date is not None:
                value['period'] = dict(
                    unit = u'year',
                    start = date,
                    )
        return value, None

    def fill_simulation(self, simulation, variables_name_to_skip = None):
        assert isinstance(simulation, simulations.Simulation)
        if variables_name_to_skip is None:
            variables_name_to_skip = set()
        column_by_name = self.tax_benefit_system.column_by_name
        entity_by_key_plural = simulation.entity_by_key_plural
        steps_count = 1
        if self.axes is not None:
            for parallel_axes in self.axes:
                # All parallel axes have the same count, entity and period.
                axis = parallel_axes[0]
                steps_count *= axis['count']
        simulation.steps_count = steps_count
        simulation_period = simulation.period
        test_case = self.test_case

        persons = None
        for entity in entity_by_key_plural.itervalues():
            entity.step_size = entity_step_size = len(test_case[entity.key_plural])
            entity.count = steps_count * entity_step_size
            if entity.is_persons_entity:
                assert persons is None
                persons = entity
        assert persons is not None
        persons_step_size = persons.step_size

        person_index_by_id = dict(
            (person[u'id'], person_index)
            for person_index, person in enumerate(test_case[persons.key_plural])
            )

        for entity_key_plural, entity in entity_by_key_plural.iteritems():
            if entity.is_persons_entity:
                continue
            entity_step_size = entity.step_size
            persons.get_or_new_holder(entity.index_for_person_variable_name).array = person_entity_id_array = np.empty(
                steps_count * persons.step_size, dtype = column_by_name[entity.index_for_person_variable_name].dtype)
            persons.get_or_new_holder(entity.role_for_person_variable_name).array = person_entity_role_array = np.empty(
                steps_count * persons.step_size, dtype = column_by_name[entity.role_for_person_variable_name].dtype)
            for member_index, member in enumerate(test_case[entity_key_plural]):
                for person_role, person_id in entity.iter_member_persons_role_and_id(member):
                    person_index = person_index_by_id[person_id]
                    for step_index in range(steps_count):
                        person_entity_id_array[step_index * persons_step_size + person_index] \
                            = step_index * entity_step_size + member_index
                        person_entity_role_array[step_index * persons_step_size + person_index] = person_role
            entity.roles_count = person_entity_role_array.max() + 1

        for entity_key_plural, entity in entity_by_key_plural.iteritems():
            used_columns_name = set(
                key
                for entity_member in test_case[entity_key_plural]
                for key, value in entity_member.iteritems()
                if value is not None and key not in (
                    entity.index_for_person_variable_name,
                    entity.role_for_person_variable_name,
                    ) and key not in variables_name_to_skip
                )
            for variable_name, column in column_by_name.iteritems():
                if column.entity == entity.symbol and variable_name in used_columns_name:
                    variable_periods = set()
                    for cell in (
                            entity_member.get(variable_name)
                            for entity_member in test_case[entity_key_plural]
                            ):
                        if isinstance(cell, dict):
                            if any(value is not None for value in cell.itervalues()):
                                variable_periods.update(cell.iterkeys())
                        elif cell is not None:
                            variable_periods.add(simulation_period)
                    holder = entity.get_or_new_holder(variable_name)
                    variable_default_value = column.default
                    for variable_period in variable_periods:
                        variable_values = [
                            variable_default_value if dated_cell is None else dated_cell
                            for dated_cell in (
                                cell.get(variable_period) if isinstance(cell, dict) else (cell
                                    if variable_period == simulation_period else None)
                                for cell in (
                                    entity_member.get(variable_name)
                                    for entity_member in test_case[entity_key_plural]
                                    )
                                )
                            ]
                        variable_values_iter = (
                            variable_value
                            for step_index in range(steps_count)
                            for variable_value in variable_values
                            )
                        array = np.fromiter(variable_values_iter, dtype = column.dtype) \
                            if column.dtype is not object \
                            else np.array(list(variable_values_iter), dtype = column.dtype)
                        holder.set_array(variable_period, array)

        if self.axes is not None:
            if len(self.axes) == 1:
                parallel_axes = self.axes[0]
                # All parallel axes have the same count, entity and period.
                first_axis = parallel_axes[0]
                axis_count = first_axis['count']
                axis_entity = simulation.entity_by_column_name[first_axis['name']]
                axis_period = first_axis['period'] or simulation_period
                for axis in parallel_axes:
                    holder = simulation.get_or_new_holder(axis['name'])
                    column = holder.column
                    array = holder.get_array(axis_period)
                    if array is None:
                        array = np.empty(axis_entity.count, dtype = column.dtype)
                        array.fill(column.default)
                        holder.set_array(axis_period, array)
                    array[axis['index']:: axis_entity.step_size] = np.linspace(axis['min'], axis['max'], axis_count)
            else:
                axes_linspaces = [
                    np.linspace(0, first_axis['count'] - 1, first_axis['count'])
                    for first_axis in (
                        parallel_axes[0]
                        for parallel_axes in self.axes
                        )
                    ]
                axes_meshes = np.meshgrid(*axes_linspaces)
                for parallel_axes, mesh in zip(self.axes, axes_meshes):
                    # All parallel axes have the same count, entity and period.
                    first_axis = parallel_axes[0]
                    axis_count = first_axis['count']
                    axis_entity = simulation.entity_by_column_name[first_axis['name']]
                    axis_period = first_axis['period'] or simulation_period
                    for axis in parallel_axes:
                        holder = simulation.get_or_new_holder(axis['name'])
                        column = holder.column
                        array = holder.get_array(axis_period)
                        if array is None:
                            array = np.empty(axis_entity.count, dtype = column.dtype)
                            array.fill(column.default)
                            holder.set_array(axis_period, array)
                        array[axis['index']:: axis_entity.step_size] = axis['min'] \
                            + mesh.reshape(steps_count) * (axis['max'] - axis['min']) / (axis_count - 1)

    def init_from_attributes(self, repair = False, **attributes):
        conv.check(self.make_json_or_python_to_attributes(repair = repair))(attributes)
        return self

    @property
    def json_or_python_to_axes(self):
        column_by_name = self.tax_benefit_system.column_by_name
        return conv.pipe(
            conv.test_isinstance(list),
            conv.uniform_sequence(
                conv.pipe(
                    conv.item_or_sequence(
                        conv.pipe(
                            conv.test_isinstance(dict),
                            conv.struct(
                                dict(
                                    count = conv.pipe(
                                        conv.test_isinstance(int),
                                        conv.test_greater_or_equal(1),
                                        conv.not_none,
                                        ),
                                    index = conv.pipe(
                                        conv.test_isinstance(int),
                                        conv.test_greater_or_equal(0),
                                        conv.default(0),
                                        ),
                                    max = conv.pipe(
                                        conv.test_isinstance((float, int)),
                                        conv.not_none,
                                        ),
                                    min = conv.pipe(
                                        conv.test_isinstance((float, int)),
                                        conv.not_none,
                                        ),
                                    name = conv.pipe(
                                        conv.test_isinstance(basestring),
                                        conv.test_in(column_by_name),
                                        conv.test(lambda column_name: column_by_name[column_name].dtype in (
                                            np.float32, np.int16, np.int32),
                                            error = N_(u'Invalid type for axe: integer or float expected')),
                                        conv.not_none,
                                        ),
                                    # TODO: Check that period is valid in params.
                                    period = periods.json_or_python_to_period,
                                    ),
                                ),
                            ),
                        drop_none_items = True,
                        ),
                    conv.make_item_to_singleton(),
                    ),
                drop_none_items = True,
                ),
            conv.empty_to_none,
            )

    def make_json_or_python_to_attributes(self, repair = False):
        column_by_name = self.tax_benefit_system.column_by_name

        def json_or_python_to_attributes(value, state = None):
            if value is None:
                return value, None
            if state is None:
                state = conv.default_state

            # First validation and conversion step
            data, error = conv.pipe(
                conv.test_isinstance(dict),
                # TODO: Remove condition below, once every calls uses "period" instead of "date" & "year".
                self.cleanup_period_in_json_or_python,
                conv.struct(
                    dict(
                        axes = self.json_or_python_to_axes,
                        period = conv.pipe(
                            periods.json_or_python_to_period,  # TODO: Check that period is valid in params.
                            conv.not_none,
                            ),
                        test_case = conv.pipe(
                            conv.test_isinstance(dict),  # Real test is done below, once period is known.
                            conv.not_none,
                            ),
                        ),
                    ),
                )(value, state = state)
            if error is not None:
                return data, error

            # Second validation and conversion step
            data, error = conv.struct(
                dict(
                    test_case = self.make_json_or_python_to_test_case(period = data['period'], repair = repair),
                    ),
                default = conv.noop,
                )(data, state = state)
            if error is not None:
                return data, error

            # Third validation and conversion step
            errors = {}
            if data['axes'] is not None:
                for parallel_axes_index, parallel_axes in enumerate(data['axes']):
                    first_axis = parallel_axes[0]
                    axis_count = first_axis['count']
                    axis_entity_key_plural = column_by_name[first_axis['name']].entity_key_plural
                    axis_period = first_axis['period']
                    for axis_index, axis in enumerate(parallel_axes):
                        if axis['min'] >= axis['max']:
                            errors.setdefault('axes', {}).setdefault(parallel_axes_index, {}).setdefault(
                                axis_index, {})['max'] = state._(u"Max value must be greater than min value")
                        column = column_by_name[axis['name']]
                        if axis['index'] >= len(data['test_case'][column.entity_key_plural]):
                            errors.setdefault('axes', {}).setdefault(parallel_axes_index, {}).setdefault(
                                axis_index, {})['index'] = state._(u"Index must be lower than {}").format(
                                    len(data['test_case'][column.entity_key_plural]))
                        if axis_index > 0:
                            if axis['count'] != axis_count:
                                errors.setdefault('axes', {}).setdefault(parallel_axes_index, {}).setdefault(
                                    axis_index, {})['count'] = state._(u"Parallel indexes must have the same count")
                            if column.entity_key_plural != axis_entity_key_plural:
                                errors.setdefault('axes', {}).setdefault(parallel_axes_index, {}).setdefault(
                                    axis_index, {})['period'] = state._(
                                        u"Parallel indexes must belong to the same entity")
                            if axis['period'] != axis_period:
                                errors.setdefault('axes', {}).setdefault(parallel_axes_index, {}).setdefault(
                                    axis_index, {})['period'] = state._(u"Parallel indexes must have the same period")
            if errors:
                return data, errors

            self.axes = data['axes']
            self.period = data['period']
            self.test_case = data['test_case']
            return self, None

        return json_or_python_to_attributes

    @classmethod
    def make_json_to_instance(cls, repair = False, tax_benefit_system = None):
        def json_to_instance(value, state = None):
            if value is None:
                return None, None
            self = cls()
            self.tax_benefit_system = tax_benefit_system
            return self.make_json_or_python_to_attributes(repair = repair)(
                value = value, state = state or conv.default_state)
        return json_to_instance

    def new_simulation(self, debug = False, debug_all = False, reference = False, trace = False):
        assert isinstance(reference, (bool, int)), \
            'Parameter reference must be a boolean. When True, the reference tax-benefit system is used.'
        tax_benefit_system = self.tax_benefit_system
        if reference:
            while True:
                reference_tax_benefit_system = tax_benefit_system.reference
                if reference_tax_benefit_system is None:
                    break
                tax_benefit_system = reference_tax_benefit_system
        simulation = simulations.Simulation(
            debug = debug,
            debug_all = debug_all,
            period = self.period,
            tax_benefit_system = tax_benefit_system,
            trace = trace,
            )
        self.fill_simulation(simulation)
        return simulation

    def to_json(self):
        return collections.OrderedDict(
            (key, value)
            for key, value in (
                (key, getattr(self, key))
                for key in (
                    'axes',
                    'period',
                    'test_case',
                    )
                )
            if value is not None
            )


def set_entities_json_id(entities_json):
    for index, entity_json in enumerate(entities_json):
        if 'id' not in entity_json:
            entity_json['id'] = index
    return entities_json
