# -*- coding: utf-8 -*-


from __future__ import division

import collections
import itertools

import numpy as np

from . import conv, periods, simulations


def N_(message):
    return message


class AbstractScenario(object):
    axes = None
    input_variables = None
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

    def fill_simulation(self, simulation, use_set_input_hooks = True, variables_name_to_skip = None):
        assert isinstance(simulation, simulations.Simulation)
        if variables_name_to_skip is None:
            variables_name_to_skip = set()
        tbs = self.tax_benefit_system
        entity_by_key_plural = simulation.entity_by_key_plural
        simulation_period = simulation.period
        test_case = self.test_case

        persons = None
        for entity in entity_by_key_plural.itervalues():
            if entity.is_persons_entity:
                assert persons is None
                persons = entity
        assert persons is not None

        if test_case is None:
            if self.input_variables is not None:
                # Note: For set_input to work, handle days, before months, before years => use sorted().
                for variable_name, array_by_period in sorted(self.input_variables.iteritems()):
                    holder = simulation.get_or_new_holder(variable_name)
                    entity = holder.entity
                    for period, array in array_by_period.iteritems():
                        if entity.count == 0:
                            entity.count = len(array)
                        if use_set_input_hooks:
                            holder.set_input(period, array)
                        else:
                            holder.put_in_cache(array, period)

            if persons.count == 0:
                persons.count = 1
            for entity in simulation.entity_by_key_plural.itervalues():
                if entity is persons:
                    continue

                index_holder = simulation.get_or_new_holder(entity.index_for_person_variable_name)
                index_array = index_holder.array
                if index_array is None:
                    index_holder.array = np.arange(persons.count, dtype = index_holder.column.dtype)

                role_holder = simulation.get_or_new_holder(entity.role_for_person_variable_name)
                role_array = role_holder.array
                if role_array is None:
                    role_holder.array = role_array = np.zeros(persons.count, role_holder.column.dtype)
                entity.roles_count = role_array.max() + 1

                if entity.count == 0:
                    entity.count = max(index_holder.array) + 1
                else:
                    assert entity.count == max(index_holder.array) + 1
        else:
            steps_count = 1
            if self.axes is not None:
                for parallel_axes in self.axes:
                    # All parallel axes have the same count, entity and period.
                    axis = parallel_axes[0]
                    steps_count *= axis['count']
            simulation.steps_count = steps_count

            for entity in entity_by_key_plural.itervalues():
                entity.step_size = entity_step_size = len(test_case[entity.key_plural])
                entity.count = steps_count * entity_step_size
            persons_step_size = persons.step_size

            person_index_by_id = dict(
                (person[u'id'], person_index)
                for person_index, person in enumerate(test_case[persons.key_plural])
                )

            for entity_key_plural, entity in entity_by_key_plural.iteritems():
                if entity.is_persons_entity:
                    continue
                entity_step_size = entity.step_size
                simulation.get_or_new_holder(entity.index_for_person_variable_name).array = person_entity_id_array = \
                    np.empty(steps_count * persons.step_size,
                        dtype = tbs.get_column(entity.index_for_person_variable_name).dtype)
                simulation.get_or_new_holder(entity.role_for_person_variable_name).array = person_entity_role_array = \
                    np.empty(steps_count * persons.step_size,
                        dtype = tbs.get_column(entity.role_for_person_variable_name).dtype)
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
                for variable_name, column in tbs.column_by_name.iteritems():
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
                        holder = simulation.get_or_new_holder(variable_name)
                        variable_default_value = column.default
                        # Note: For set_input to work, handle days, before months, before years => use sorted().
                        for variable_period in sorted(variable_periods):
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
                            if use_set_input_hooks:
                                holder.set_input(variable_period, array)
                            else:
                                holder.put_in_cache(array, variable_period)

            if self.axes is not None:
                if len(self.axes) == 1:
                    parallel_axes = self.axes[0]
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
                        array[axis['index']:: axis_entity.step_size] = np.linspace(axis['min'], axis['max'], axis_count)
                        if use_set_input_hooks:
                            holder.set_input(axis_period, array)
                        else:
                            holder.put_in_cache(array, axis_period)
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

    def init_from_attributes(self, repair = False, **attributes):
        conv.check(self.make_json_or_python_to_attributes(repair = repair))(attributes)
        return self

    def make_json_or_python_to_attributes(self, repair = False):
        tbs = self.tax_benefit_system

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
                        axes = make_json_or_python_to_axes(self.tax_benefit_system),
                        input_variables = conv.test_isinstance(dict),  # Real test is done below, once period is known.
                        period = conv.pipe(
                            periods.json_or_python_to_period,  # TODO: Check that period is valid in params.
                            conv.not_none,
                            ),
                        test_case = conv.test_isinstance(dict),  # Real test is done below, once period is known.
                        ),
                    ),
                )(value, state = state)
            if error is not None:
                return data, error

            # Second validation and conversion step
            data, error = conv.struct(
                dict(
                    input_variables = make_json_or_python_to_input_variables(self.tax_benefit_system, data['period']),
                    test_case = self.make_json_or_python_to_test_case(period = data['period'], repair = repair),
                    ),
                default = conv.noop,
                )(data, state = state)
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
                    axis_entity_key_plural = tbs.get_column(first_axis['name']).entity_key_plural
                    first_axis_period = first_axis['period'] or data['period']
                    for axis_index, axis in enumerate(parallel_axes):
                        if axis['min'] >= axis['max']:
                            errors.setdefault('axes', {}).setdefault(parallel_axes_index, {}).setdefault(
                                axis_index, {})['max'] = state._(u"Max value must be greater than min value")
                        column = tbs.get_column(axis['name'])
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

    def new_simulation(self, debug = False, debug_all = False, reference = False, trace = False,
            use_set_input_hooks = True, opt_out_cache = False):
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
            opt_out_cache = opt_out_cache,
            )
        self.fill_simulation(simulation, use_set_input_hooks = use_set_input_hooks)
        return simulation

    def to_json(self):
        return collections.OrderedDict(
            (key, value)
            for key, value in (
                (key, getattr(self, key))
                for key in (
                    'period',
                    'input_variables',
                    'test_case',
                    'axes',
                    )
                )
            if value is not None
            )


def extract_output_variables_name_to_ignore(output_variables_name_to_ignore):
    def extract_output_variables_name_to_ignore_converter(value, state = None):
        if value is None:
            return value, None

        new_value = collections.OrderedDict()
        for variable_name, variable_value in value.iteritems():
            if variable_name.startswith(u'IGNORE_'):
                variable_name = variable_name[len(u'IGNORE_'):]
                output_variables_name_to_ignore.add(variable_name)
            new_value[variable_name] = variable_value
        return new_value, None

    return extract_output_variables_name_to_ignore_converter


def make_json_or_python_to_array_by_period_by_variable_name(tax_benefit_system, period):
    def json_or_python_to_array_by_period_by_variable_name(value, state = None):
        if value is None:
            return value, None
        if state is None:
            state = conv.default_state
        error_by_variable_name = {}
        array_by_period_by_variable_name = collections.OrderedDict()
        for variable_name, variable_value in value.iteritems():
            column = tax_benefit_system.get_column(variable_name)
            if isinstance(variable_value, np.ndarray):
                variable_array_by_period = {period: variable_value}
            else:
                variable_array_by_period, error = column.make_json_to_array_by_period(period)(
                    variable_value, state = state)
                if error is not None:
                    error_by_variable_name[variable_name] = error
            if variable_array_by_period is not None:
                array_by_period_by_variable_name[variable_name] = variable_array_by_period
        return array_by_period_by_variable_name, error_by_variable_name or None

    return json_or_python_to_array_by_period_by_variable_name


def make_json_or_python_to_axes(tax_benefit_system):
    column_by_name = tax_benefit_system.column_by_name
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
                                    conv.test(lambda column_name: tax_benefit_system.get_column(column_name).dtype in (
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


def make_json_or_python_to_input_variables(tax_benefit_system, period):
    column_by_name = tax_benefit_system.column_by_name
    variables_name = set(column_by_name)

    def json_or_python_to_input_variables(value, state = None):
        if value is None:
            return value, None
        if state is None:
            state = conv.default_state

        input_variables, errors = conv.pipe(
            conv.test_isinstance(dict),
            conv.uniform_mapping(
                conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.test_in(variables_name),
                    conv.not_none,
                    ),
                conv.noop,
                ),
            make_json_or_python_to_array_by_period_by_variable_name(tax_benefit_system, period),
            conv.empty_to_none,
            )(value, state = state)
        if errors is not None:
            return input_variables, errors
        if input_variables is None:
            return input_variables, None

        count_by_entity_key_plural = {}
        errors = {}
        for variable_name, array_by_period in input_variables.iteritems():
            column = tax_benefit_system.get_column(variable_name)
            entity_key_plural = column.entity_key_plural
            entity_count = count_by_entity_key_plural.get(entity_key_plural, 0)
            for variable_period, variable_array in array_by_period.iteritems():
                if entity_count == 0:
                    count_by_entity_key_plural[entity_key_plural] = entity_count = len(variable_array)
                elif len(variable_array) != entity_count:
                    errors[column.name] = state._(
                        u"Array has not the same length as other variables of entity {}: {} instead of {}").format(
                            column.name, len(variable_array), entity_count)

        return input_variables, errors or None

    return json_or_python_to_input_variables


def make_json_or_python_to_test(tax_benefit_system, default_absolute_error_margin = None,
        default_relative_error_margin = None):
    column_by_name = tax_benefit_system.column_by_name
    variables_name = set(column_by_name)
    validate = conv.struct(
        dict(itertools.chain(
            dict(
                absolute_error_margin = conv.pipe(
                    conv.test_isinstance((float, int)),
                    conv.test_greater_or_equal(0),
                    ),
                axes = make_json_or_python_to_axes(tax_benefit_system),
                description = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_line,
                    ),
                ignore = conv.pipe(
                    conv.test_isinstance((bool, int)),
                    conv.anything_to_bool,
                    ),
                input_variables = conv.pipe(
                    conv.test_isinstance(dict),
                    conv.uniform_mapping(
                        conv.pipe(
                            conv.test_isinstance(basestring),
                            conv.test_in(variables_name),
                            conv.not_none,
                            ),
                        conv.noop,
                        ),
                    conv.empty_to_none,
                    ),
                keywords = conv.pipe(
                    conv.make_item_to_singleton(),
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        conv.pipe(
                            conv.test_isinstance(basestring),
                            conv.cleanup_line,
                            ),
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    ),
                name = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_line,
                    ),
                output_variables = conv.test_isinstance(dict),
                period = conv.pipe(
                    periods.json_or_python_to_period,
                    conv.not_none,
                    ),
                relative_error_margin = conv.pipe(
                    conv.test_isinstance((float, int)),
                    conv.test_greater_or_equal(0),
                    ),
                ).iteritems(),
            (
                (entity_class.key_plural, conv.pipe(
                    conv.make_item_to_singleton(),
                    conv.test_isinstance(list),
                    ))
                for entity_class in tax_benefit_system.entity_class_by_key_plural.itervalues()
                ),
            )),
        )

    def json_or_python_to_test(value, state = None):
        if value is None:
            return value, None
        if state is None:
            state = conv.default_state
        output_variables_name_to_ignore = set()
        value, error = conv.pipe(
            conv.test_isinstance(dict),
            conv.struct(
                dict(
                    output_variables = extract_output_variables_name_to_ignore(output_variables_name_to_ignore),
                    ),
                default = conv.noop,
                ),
            validate,
            )(value, state = state)
        if error is not None:
            return value, error

        value, error = conv.struct(
            dict(
                output_variables = make_json_or_python_to_input_variables(tax_benefit_system, value['period']),
                ),
            default = conv.noop,
            )(value, state = state)
        if error is not None:
            return value, error

        test_case = value.copy()
        absolute_error_margin = test_case.pop(u'absolute_error_margin')
        axes = test_case.pop(u'axes')
        description = test_case.pop(u'description')
        ignore = test_case.pop(u'ignore')
        input_variables = test_case.pop(u'input_variables')
        keywords = test_case.pop(u'keywords')
        name = test_case.pop(u'name')
        output_variables = test_case.pop(u'output_variables')
        period = test_case.pop(u'period')
        relative_error_margin = test_case.pop(u'relative_error_margin')

        if absolute_error_margin is None and relative_error_margin is None:
            absolute_error_margin = default_absolute_error_margin
            relative_error_margin = default_relative_error_margin

        if test_case is not None and all(entity_members is None for entity_members in test_case.itervalues()):
            test_case = None

        scenario, error = tax_benefit_system.Scenario.make_json_to_instance(repair = True,
            tax_benefit_system = tax_benefit_system)(dict(
                axes = axes,
                input_variables = input_variables,
                period = period,
                test_case = test_case,
                ), state = state)
        if error is not None:
            return scenario, error

        return {
            key: value
            for key, value in dict(
                absolute_error_margin = absolute_error_margin,
                description = description,
                ignore = ignore,
                keywords = keywords,
                name = name,
                output_variables = output_variables,
                output_variables_name_to_ignore = output_variables_name_to_ignore,
                relative_error_margin = relative_error_margin,
                scenario = scenario,
                ).iteritems()
            if value is not None
            }, None

    return json_or_python_to_test


def set_entities_json_id(entities_json):
    for index, entity_json in enumerate(entities_json):
        if 'id' not in entity_json:
            entity_json['id'] = index
    return entities_json
