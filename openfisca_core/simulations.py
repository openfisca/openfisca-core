# -*- coding: utf-8 -*-

import collections

import numpy as np

from . import periods, holders, conv


def N_(message):
    return message


class AbstractSimulation(object):
    compact_legislation_by_instant_cache = None
    reference_compact_legislation_by_instant_cache = None

    def __init__(self, tbs=None):
        # concrete class constructor already built a test case (or input_values, not tested yet)

        assert tbs is not None
        self.tax_benefit_system = tbs

        # Note: Since simulations are short-lived and must be fast, don't use weakrefs for cache.
        self.compact_legislation_by_instant_cache = {}
        self.reference_compact_legislation_by_instant_cache = {}

        self.entities = tbs.entities

        self.entity_data = dict(
            (entity, {'count': None})
            for entity in self.entities
            )
        entity_data = self.entity_data

        self.persons = None
        for entity in self.entities:
            if dict(entity).get('is_persons_entity'):
                assert self.persons is None
                self.persons = entity
        assert self.persons is not None
        persons = self.persons

        test_case = self.test_case

        self.variable_by_name = {}
        variable_by_name = self.variable_by_name

        if test_case is None:   # WARNING ! not tested !
            raise Exception('not ready yet')
            if self.input_variables is not None:
                # Note: For set_input to work, handle days, before months, before years => use sorted().
                for variable_name, array_by_period in sorted(self.input_variables.iteritems()):
                    holder = self.get_or_new_holder(variable_name)
                    entity = holder.entity
                    for period, array in array_by_period.iteritems():
                        if entity_data[entity]['count'] == 0:
                            entity.count = len(array)
                        if use_set_input_hooks:
                            holder.set_input(period, array)
                        else:
                            holder.put_in_cache(array, period)

            assert self.entity_data[self.persons] is None
            self.entity_data[self.persons]['count'] = 1
            for entity in self.entities:
                if entity is self.persons:
                    continue

                index_holder = self.get_or_new_holder(entity.index_for_person_variable_name)
                index_array = index_holder.array
                if index_array is None:
                    index_holder.array = np.arange(self.entity_data[self.persons]['count'], dtype=index_holder.column.dtype)

                role_holder = self.get_or_new_holder(entity.role_for_person_variable_name)
                role_array = role_holder.array
                if role_array is None:
                    role_holder.array = role_array = np.zeros(self.entity_data[self.persons]['count'], role_holder.column.dtype)
                self.entity_data[entity]['roles_count'] = role_array.max() + 1

                if self.entity_data[entity]['count'] == 0:
                    self.entity_data[entity]['count'] = max(index_holder.array) + 1
                else:
                    assert self.entity_data[entity]['count'] == max(index_holder.array) + 1
        else:  # if test case
            # instantiate all the variable classes
            for variable_name, variable_class in tbs.variable_class_by_name.items():
                variable_by_name[variable_name] = variable_class(self)

            steps_count = 1
            if self.axes is not None:
                for parallel_axes in self.axes:
                    # All parallel axes have the same count, entity and period.
                    axis = parallel_axes[0]
                    steps_count *= axis['count']
            self.steps_count = steps_count

            for entity in self.entities:
                entity_data[entity]['step_size'] = entity_step_size = len(test_case[dict(entity)['key_plural']])
                entity_data[entity]['count'] = steps_count * entity_step_size
            persons_step_size = entity_data[persons]['step_size']

            person_index_by_id = dict(
                (person[u'id'], person_index)
                for person_index, person in enumerate(test_case[dict(persons)['key_plural']])
                )

            for entity in self.entities:
                if dict(entity).get('is_persons_entity'):
                    continue
                entity_step_size = entity_data[entity]['step_size']

                # person->entity table
                index_variable = variable_by_name[dict(entity)['index_for_person_variable_name']]
                index_array = np.empty(steps_count * entity_data[persons]['step_size'],
                                       dtype=index_variable.dtype)

                # person->role-in-entity table
                role_variable = variable_by_name[dict(entity)['role_for_person_variable_name']]
                role_array = np.empty(steps_count * entity_data[persons]['step_size'],
                                      dtype=index_variable.dtype)

                for member_index, member in enumerate(test_case[dict(entity)['key_plural']]):
                    for person_role, person_id in dict(entity)['iter_member_persons_role_and_id'](member):
                        person_index = person_index_by_id[person_id]
                        for step_index in range(steps_count):
                            index_array[step_index * persons_step_size + person_index] \
                                = step_index * entity_step_size + member_index
                            role_array[step_index * persons_step_size + person_index] = person_role

                index_variable.set_input(index_array)
                role_variable.set_input(role_array)

                entity_data[entity]['roles_count'] = role_array.max() + 1

            for entity in self.entities:
                used_columns_name = set(
                    key
                    for entity_member in test_case[dict(entity)['key_plural']]
                    for key, value in entity_member.iteritems()
                    if value is not None and key not in (
                        dict(entity)['index_for_person_variable_name'],
                        dict(entity)['role_for_person_variable_name'],
                        )
                    )
                for variable_name, variable in variable_by_name.items():
                    if variable.entity is entity and variable_name in used_columns_name:
                        variable_periods = set()
                        for cell in (
                                entity_member.get(variable_name)
                                for entity_member in test_case[dict(entity)['key_plural']]
                                ):
                            if isinstance(cell, dict):
                                if any(value is not None for value in cell.itervalues()):
                                    variable_periods.update(cell.iterkeys())
                            elif cell is not None:
                                variable_periods.add(self.period)
                        variable_default_value = variable.default
                        # Note: For set_input to work, handle days, before months, before years => use sorted().
                        for variable_period in sorted(variable_periods):
                            variable_values = [
                                variable_default_value if dated_cell is None else dated_cell
                                for dated_cell in (
                                    cell.get(variable_period) if isinstance(cell, dict) else (cell
                                        if variable_period == self.period else None)
                                    for cell in (
                                        entity_member.get(variable_name)
                                        for entity_member in test_case[dict(entity)['key_plural']]
                                        )
                                    )
                                ]
                            variable_values_iter = (
                                variable_value
                                for step_index in range(steps_count)
                                for variable_value in variable_values
                                )
                            array = np.fromiter(variable_values_iter, dtype=variable.dtype) \
                                if variable.dtype is not object \
                                else np.array(list(variable_values_iter), dtype=variable.dtype)
                            variable.set_value(array, period=variable_period)

            if self.axes is not None:
                if len(self.axes) == 1:
                    parallel_axes = self.axes[0]
                    # All parallel axes have the same count and entity.
                    first_axis = parallel_axes[0]
                    axis_count = first_axis['count']
                    axis_entity = variable_by_name[first_axis['name']].entity
                    for axis in parallel_axes:
                        axis_period = axis['period'] or self.period
                        variable = variable_by_name[axis['name']]
                        array = holder.get_value(period=axis_period)
                        if array is None:
                            array = np.empty(entity_data[axis_entity]['count'], dtype=variable.dtype)
                            array.fill(variable.default)
                        array[axis['index']::entity_data[axis_entity]['step_size']] = np.linspace(axis['min'], axis['max'], axis_count)
                        variable.set_value(array, period=axis_period)
                else:
                    # first_axis : local binding error ?
                    raise Exception('not ready yet')

                    axes_linspaces = [
                        np.linspace(0, first_axis['count'] - 1, first_axis['count'])
                        for first_axis in (
                            parallel_axes[0]
                            for parallel_axes in self.axes
                            )
                        ]
                    axes_meshes = np.meshgrid(*axes_linspaces)
                    for parallel_axes, mesh in zip(self.axes, axes_meshes):
                        # All parallel axes have the same count and entity.
                        first_axis = parallel_axes[0]
                        axis_count = first_axis['count']
                        axis_entity = simulation.get_variable_entity(first_axis['name'])
                        for axis in parallel_axes:
                            axis_period = axis['period'] or simulation_period
                            holder = simulation.get_or_new_holder(axis['name'])
                            column = holder.column
                            array = holder.get_array(axis_period)
                            if array is None:
                                array = np.empty(axis_entity.count, dtype = column.dtype)
                                array.fill(column.default)
                            array[axis['index']:: axis_entity.step_size] = axis['min'] \
                                + mesh.reshape(steps_count) * (axis['max'] - axis['min']) / (axis_count - 1)
                            if use_set_input_hooks:
                                holder.set_input(axis_period, array)
                            else:
                                holder.put_in_cache(array, axis_period)

    def calculate(self, variable_name, period=None, **parameters):
        variable = self.variable_by_name[variable_name]
        return variable.calculate(period=period, **parameters)

    def get_compact_legislation(self, instant):
        compact_legislation = self.compact_legislation_by_instant_cache.get(instant)
        if compact_legislation is None:
            compact_legislation = self.tax_benefit_system.get_compact_legislation(
                instant = instant,
                traced_simulation = self if self.trace else None,
                )
            self.compact_legislation_by_instant_cache[instant] = compact_legislation
        return compact_legislation

    def get_reference_compact_legislation(self, instant):
        reference_compact_legislation = self.reference_compact_legislation_by_instant_cache.get(instant)
        if reference_compact_legislation is None:
            reference_compact_legislation = self.tax_benefit_system.get_reference_compact_legislation(
                instant = instant,
                traced_simulation = self if self.trace else None,
                )
            self.reference_compact_legislation_by_instant_cache[instant] = reference_compact_legislation
        return reference_compact_legislation

    def legislation_at(self, instant, reference = False):
        assert isinstance(instant, periods.Instant), "Expected an instant. Got: {}".format(instant)
        if reference:
            return self.get_reference_compact_legislation(instant)
        return self.get_compact_legislation(instant)

    @staticmethod
    def cleanup_period_in_json_or_python(value, state=None):
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
                    unit=u'year',
                    start=date,
                    )
        return value, None

    def make_json_or_python_to_attributes(self, repair=False):
        tbs = self.tax_benefit_system

        def json_or_python_to_attributes(value, state=None):
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
                        axes=make_json_or_python_to_axes(self.tax_benefit_system),
                        input_variables=conv.test_isinstance(dict),  # Real test is done below, once period is known.
                        period=conv.pipe(
                            periods.json_or_python_to_period,  # TODO: Check that period is valid in params.
                            conv.not_none,
                            ),
                        test_case=conv.test_isinstance(dict),  # Real test is done below, once period is known.
                        ),
                    ),
                )(value, state=state)
            if error is not None:
                return data, error

            # Second validation and conversion step
            data, error = conv.struct(
                dict(
                    input_variables=make_json_or_python_to_input_variables(self.tax_benefit_system, data['period']),
                    test_case=self.make_json_or_python_to_test_case(period=data['period'], repair=repair),
                    ),
                default=conv.noop,
                )(data, state=state)
            if error is not None:
                return data, error

            # Third validation and conversion step
            errors = {}
            if data['input_variables'] is not None and data['test_case'] is not None:
                errors['input_variables'] = state._(u"Items input_variables and test_case can't both exist")
                errors['test_case'] = state._(u"Items input_variables and test_case can't both exist")
            elif data['axes'] is not None and data["test_case"] is None:
                errors['axes'] = state._(u"Axes can't be used with input_variables.")
            if errors:
                return data, errors

            if data['axes'] is not None:
                for parallel_axes_index, parallel_axes in enumerate(data['axes']):
                    first_axis = parallel_axes[0]
                    axis_count = first_axis['count']
                    axis_entity_key_plural = dict(tbs.get_variable_class(first_axis['name']).entity)['key_plural']
                    first_axis_period = first_axis['period'] or data['period']
                    for axis_index, axis in enumerate(parallel_axes):
                        if axis['min'] >= axis['max']:
                            errors.setdefault('axes', {}).setdefault(parallel_axes_index, {}).setdefault(
                                axis_index, {})['max'] = state._(u"Max value must be greater than min value")
                        variable_class = tbs.get_variable_class(axis['name'])
                        if axis['index'] >= len(data['test_case'][dict(variable_class.entity)['key_plural']]):
                            errors.setdefault('axes', {}).setdefault(parallel_axes_index, {}).setdefault(
                                axis_index, {})['index'] = state._(u"Index must be lower than {}").format(
                                    len(data['test_case'][dict(variable_class.entity)['key_plural']]))
                        if axis_index > 0:
                            if axis['count'] != axis_count:
                                errors.setdefault('axes', {}).setdefault(parallel_axes_index, {}).setdefault(
                                    axis_index, {})['count'] = state._(u"Parallel indexes must have the same count")
                            if dict(variable_class.entity)['key_plural'] != axis_entity_key_plural:
                                errors.setdefault('axes', {}).setdefault(parallel_axes_index, {}).setdefault(
                                    axis_index, {})['period'] = state._(
                                        u"Parallel indexes must belong to the same entity")
                            axis_period = axis['period'] or data['period']
                            if axis_period.unit != first_axis_period.unit:
                                errors.setdefault('axes', {}).setdefault(parallel_axes_index, {}).setdefault(
                                    axis_index, {})['period'] = state._(
                                        u"Parallel indexes must have the same period unit")
                            elif axis_period.size != first_axis_period.size:
                                errors.setdefault('axes', {}).setdefault(parallel_axes_index, {}).setdefault(
                                    axis_index, {})['period'] = state._(
                                        u"Parallel indexes must have the same period size")
                if errors:
                    return data, errors

            self.axes = data['axes']
            if data['input_variables'] is not None:
                self.input_variables = data['input_variables']
            self.period = data['period']
            if data['test_case'] is not None:
                self.test_case = data['test_case']
            return self, None

        return json_or_python_to_attributes


def make_json_or_python_to_axes(tax_benefit_system):
    variable_class_by_name = tax_benefit_system.variable_class_by_name
    return conv.pipe(
        conv.test_isinstance(list),
        conv.uniform_sequence(
            conv.pipe(
                conv.item_or_sequence(
                    conv.pipe(
                        conv.test_isinstance(dict),
                        conv.struct(
                            dict(
                                count=conv.pipe(
                                    conv.test_isinstance(int),
                                    conv.test_greater_or_equal(1),
                                    conv.not_none,
                                    ),
                                index=conv.pipe(
                                    conv.test_isinstance(int),
                                    conv.test_greater_or_equal(0),
                                    conv.default(0),
                                    ),
                                max=conv.pipe(
                                    conv.test_isinstance((float, int)),
                                    conv.not_none,
                                    ),
                                min=conv.pipe(
                                    conv.test_isinstance((float, int)),
                                    conv.not_none,
                                    ),
                                name=conv.pipe(
                                    conv.test_isinstance(basestring),
                                    conv.test_in(variable_class_by_name),
                                    conv.test(lambda variable_class_name: tax_benefit_system.get_variable_class(variable_class_name).dtype in (
                                        np.float32, np.int16, np.int32),
                                        error=N_(u'Invalid type for axe: integer or float expected')),
                                    conv.not_none,
                                    ),
                                # TODO: Check that period is valid in params.
                                period=periods.json_or_python_to_period,
                                ),
                            ),
                        ),
                    drop_none_items=True,
                    ),
                conv.make_item_to_singleton(),
                ),
            drop_none_items=True,
            ),
        conv.empty_to_none,
        )

def make_json_or_python_to_input_variables(tax_benefit_system, period):
    variable_class_by_name = tax_benefit_system.variable_class_by_name
    variable_class_names = set(variable_class_by_name)

    def json_or_python_to_input_variables(value, state=None):
        if value is None:
            return value, None
        if state is None:
            state = conv.default_state

        raise Exception('boom!')

        input_variables, errors = conv.pipe(
            conv.test_isinstance(dict),
            conv.uniform_mapping(
                conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.test_in(variable_class_names),
                    conv.not_none,
                    ),
                conv.noop,
                ),
            make_json_or_python_to_array_by_period_by_variable_name(tax_benefit_system, period),
            conv.empty_to_none,
            )(value, state=state)
        if errors is not None:
            return input_variables, errors
        if input_variables is None:
            return input_variables, None

        count_by_entity = {}
        errors = {}
        for variable_name, array_by_period in input_variables.iteritems():
            variable_class = tax_benefit_system.get_variable_class(variable_name)
            entity = variable_class.entity
            entity_count = count_by_entity.get(entity, 0)
            for variable_period, variable_array in array_by_period.iteritems():
                if entity_count == 0:
                    count_by_entity[entity] = entity_count = len(variable_array)
                elif len(variable_array) != entity_count:
                    errors[variable_class.name] = state._(
                        u"Array has not the same length as other variables of entity {}: {} instead of {}").format(
                            variable_class.name, len(variable_array), entity_count)

        return input_variables, errors or None

    return json_or_python_to_input_variables

def make_json_or_python_to_array_by_period_by_variable_name(tax_benefit_system, period):
    def json_or_python_to_array_by_period_by_variable_name(value, state=None):
        if value is None:
            return value, None
        if state is None:
            state = conv.default_state
        error_by_variable_name = {}
        array_by_period_by_variable_name = collections.OrderedDict()
        for variable_name, variable_value in value.iteritems():
            variable_class = tax_benefit_system.get_variable_class(variable_name)
            if isinstance(variable_value, np.ndarray):
                variable_array_by_period = {period: variable_value}
            else:
                variable_array_by_period, error = variable_class.make_json_to_array_by_period(period)(
                    variable_value, state=state)
                if error is not None:
                    error_by_variable_name[variable_name] = error
            if variable_array_by_period is not None:
                array_by_period_by_variable_name[variable_name] = variable_array_by_period
        return array_by_period_by_variable_name, error_by_variable_name or None

    return json_or_python_to_array_by_period_by_variable_name

def set_entities_json_id(entities_json):
    for index, entity_json in enumerate(entities_json):
        if 'id' not in entity_json:
            entity_json['id'] = index
    return entities_json
