# -*- coding: utf-8 -*-


from __future__ import division

import collections
import itertools

import numpy as np

from . import conv, periods, simulations, json_to_test_case


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
                value['period'] = periods.period(date)
        return value, None

    def fill_simulation(self, simulation):
        assert isinstance(simulation, simulations.Simulation)
        tbs = self.tax_benefit_system
        simulation_period = simulation.period
        test_case = self.test_case

        persons = simulation.persons

        if test_case is None:
            if self.input_variables is not None:
                # Note: For set_input to work, handle days, before months, before years => use sorted().
                for variable_name, array_by_period in sorted(self.input_variables.iteritems()):
                    holder = simulation.get_or_new_holder(variable_name)
                    entity = holder.entity
                    for period, array in array_by_period.iteritems():
                        if entity.count == 0:
                            entity.count = len(array)
                        holder.set_input(period, array)

            if persons.count == 0:
                persons.count = 1

            for entity in simulation.entities.itervalues():
                if entity is persons:
                    continue

                if entity.members_entity_id is None:
                    entity.members_entity_id = np.arange(persons.count, dtype = np.int32)

                if entity.members_role is None:
                    default_role = entity.roles[0] if entity.roles[0].subroles is None else entity.roles[0].subroles[0]
                    entity.members_role = np.full(persons.count, default_role, dtype = object)
                entity.roles_count = len(np.unique(entity.members_role))

                if entity.members_legacy_role is None:
                    entity.members_legacy_role = np.zeros(persons.count, dtype = np.int32)

                if entity.count == 0:
                    entity.count = max(entity.members_entity_id) + 1
                else:
                    assert entity.count == max(entity.members_entity_id) + 1
        else:
            steps_count = 1
            if self.axes is not None:
                # See set_input function comment below
                # defaultdict(dict) is like dict but returns {} when calling d[k] if d[k] is not yet defined
                cache_buffer = collections.defaultdict(dict)
                for parallel_axes in self.axes:
                    # All parallel axes have the same count, entity and period.
                    axis = parallel_axes[0]
                    steps_count *= axis['count']
            simulation.steps_count = steps_count

            # When we use axes, we use a buffer for the cache, to avoid collisions between several calls of holder.set_input.
            def set_input(variable_name, period, value):
                if self.axes is not None:
                    cache_buffer[variable_name][period] = value
                else:
                    holder = simulation.get_or_new_holder(variable_name)
                    holder.set_input(period, value)

            for entity in simulation.entities.itervalues():
                step_size = len(test_case[entity.plural])
                count = steps_count * step_size
                entity.count = count
                entity.step_size = step_size

            persons_step_size = persons.step_size

            person_index_by_id = dict(
                (person[u'id'], person_index)
                for person_index, person in enumerate(test_case[persons.plural])
                )

            for entity in simulation.entities.itervalues():

                used_columns_name = set(
                    key
                    for entity_member in test_case[entity.plural]
                    for key, value in entity_member.iteritems()
                    if value is not None
                    )

                if not entity.is_person:

                    entity_step_size = entity.step_size

                    entity.members_entity_id = np.empty(
                        steps_count * persons_step_size,
                        dtype = np.int32
                        )
                    entity.members_role = np.empty(
                        steps_count * persons_step_size,
                        dtype = object
                        )
                    entity.members_legacy_role = np.empty(
                        steps_count * persons_step_size,
                        dtype = np.int32
                        )

                    for scenario_entity_index, scenario_entity in enumerate(test_case[entity.plural]):
                        for person_role, person_legacy_role, person_id in iter_over_entity_members(entity, scenario_entity):
                            person_index = person_index_by_id[person_id]
                            for step_index in range(steps_count):
                                individu_index = step_index * persons_step_size + person_index

                                entity.members_entity_id[individu_index] = step_index * entity_step_size + scenario_entity_index
                                entity.members_role[individu_index] = person_role
                                entity.members_legacy_role[individu_index] = person_legacy_role
                    entity.roles_count = entity.members_legacy_role.max() + 1

                for variable_name, column in tbs.column_by_name.iteritems():
                    if column.entity == entity.__class__ and variable_name in used_columns_name:
                        variable_periods = set()
                        for cell in (
                                entity_member.get(variable_name)
                                for entity_member in test_case[entity.plural]
                                ):
                            if isinstance(cell, dict):
                                if any(value is not None for value in cell.itervalues()):
                                    variable_periods.update(cell.iterkeys())
                            elif cell is not None:
                                variable_periods.add(simulation_period)
                        variable_default_value = column.default
                        # Note: For set_input to work, handle days, before months, before years => use sorted().
                        for variable_period in sorted(variable_periods, cmp = periods.compare_period_size):
                            variable_values = [
                                variable_default_value if dated_cell is None else dated_cell
                                for dated_cell in (
                                    cell.get(variable_period) if isinstance(cell, dict) else (cell
                                        if variable_period == simulation_period else None)
                                    for cell in (
                                        entity_member.get(variable_name)
                                        for entity_member in test_case[entity.plural]
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
                            set_input(variable_name, variable_period, array)

            if self.axes is not None:
                if len(self.axes) == 1:
                    parallel_axes = self.axes[0]
                    # All parallel axes have the same count and entity.
                    first_axis = parallel_axes[0]
                    axis_count = first_axis['count']
                    axis_entity = simulation.get_variable_entity(first_axis['name'])
                    axis_entity_count = axis_entity.count
                    axis_entity_step_size = axis_entity.step_size
                    for axis in parallel_axes:
                        axis_period = axis['period'] or simulation_period
                        axis_name = axis['name']
                        array = cache_buffer[axis_name].get(axis_period)
                        if array is None:
                            column = tbs.column_by_name[axis_name]
                            array = np.empty(axis_entity_count, dtype = column.dtype)
                            array.fill(column.default)
                        array[axis['index']:: axis_entity_step_size] = np.linspace(axis['min'], axis['max'], axis_count)
                        cache_buffer[axis_name][axis_period] = array
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
                        axis_entity_count = axis_entity.count
                        axis_entity_step_size = axis_entity.step_size
                        for axis in parallel_axes:
                            axis_period = axis['period'] or simulation_period
                            axis_name = axis['name']
                            array = cache_buffer[axis_name].get(axis_period)
                            if array is None:
                                column = tbs.column_by_name[axis_name]
                                array = np.empty(axis_entity_count, dtype = column.dtype)
                                array.fill(column.default)
                            array[axis['index']:: axis_entity_step_size] = axis['min'] \
                                + mesh.reshape(steps_count) * (axis['max'] - axis['min']) / (axis_count - 1)
                            cache_buffer[axis_name][axis_period] = array

                # We pour the buffer in the real cache
                for variable, values in cache_buffer.iteritems():
                    holder = simulation.get_or_new_holder(variable)
                    for period, array in values.iteritems():
                        holder.set_input(period, array)

    def init_from_attributes(self, repair = False, **attributes):
        conv.check(self.make_json_or_python_to_attributes(repair = repair))(attributes)
        return self

    def init_from_test_case(self, period, test_case):
        conv.check(self.make_json_or_python_to_attributes())(dict(
            period = period,
            test_case = test_case
            ))
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
                            conv.function(periods.period),
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
                    axis_entity_key = tbs.get_column(first_axis['name']).entity.key
                    first_axis_period = first_axis['period'] or data['period']
                    for axis_index, axis in enumerate(parallel_axes):
                        if axis['min'] >= axis['max']:
                            errors.setdefault('axes', {}).setdefault(parallel_axes_index, {}).setdefault(
                                axis_index, {})['max'] = state._(u"Max value must be greater than min value")
                        column = tbs.get_column(axis['name'])
                        if axis['index'] >= len(data['test_case'][column.entity.plural]):
                            errors.setdefault('axes', {}).setdefault(parallel_axes_index, {}).setdefault(
                                axis_index, {})['index'] = state._(u"Index must be lower than {}").format(
                                    len(data['test_case'][column.entity.plural]))
                        if axis_index > 0:
                            if axis['count'] != axis_count:
                                errors.setdefault('axes', {}).setdefault(parallel_axes_index, {}).setdefault(
                                    axis_index, {})['count'] = state._(u"Parallel indexes must have the same count")
                            if column.entity.key != axis_entity_key:
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

    def new_simulation(self, debug = False, debug_all = False, reference = False, trace = False, opt_out_cache = False):
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
        self.fill_simulation(simulation)
        return simulation

    def make_json_or_python_to_test_case(self, period, repair = False):
        def json_or_python_to_test_case(value, state = None):
            if value is None:
                return value, None
            if state is None:
                state = conv.default_state

            test_case = json_to_test_case.check_entities_and_role(value, self.tax_benefit_system, state)

            test_case, error, groupless_persons = json_to_test_case.check_entities_consistency(test_case, self.tax_benefit_system, state)
            if error is not None:
                return test_case, error

            # We try to attribute groupless individus to entities, according to rules defined by each country
            if repair:
                test_case = self.attribute_groupless_persons_to_entities(test_case, period, groupless_persons)

            test_case, error = json_to_test_case.check_each_person_has_entities(test_case, self.tax_benefit_system, state)
            if error is not None:
                return test_case, error

            test_case, error = self.post_process_test_case(test_case, period, state)

            return test_case, error

        return json_or_python_to_test_case

    def to_json(self):
        self_json = {}
        if self.axes is not None:
            self_json['axes'] = self.axes
        if self.period is not None:
            self_json['period'] = str(self.period)

        test_case = self.test_case
        if test_case is not None:
            column_by_name = self.tax_benefit_system.column_by_name
            test_case_json = {}

            for entity_type in self.tax_benefit_system.entities:
                entities_json = []
                for entity in (test_case.get(entity_type.plural) or []):
                    entity_json = {}
                    entity_json['id'] = entity['id']
                    if not entity_type.is_person:
                        for role in entity_type.roles:
                            if entity.get(role.plural or role.key):
                                entity_json[role.plural or role.key] = entity.get(role.plural or role.key)
                    for column_name, variable_value in entity.iteritems():
                        column = column_by_name.get(column_name)
                        if column is not None and column.entity == entity_type:
                            variable_value_json = column.transform_value_to_json(variable_value)
                            if variable_value_json is not None:
                                entity_json[column_name] = variable_value_json
                    entities_json.append(entity_json)
                if entities_json:
                    test_case_json[entity_type.plural] = entities_json

            self_json['test_case'] = test_case_json
        return self_json

    def suggest(self):
        pass  # To be reimplemented

    def attribute_groupless_persons_to_entities(self, test_case, period, groupless_persons):
        """
            Tries to reattribute persons who don't have an entity of each kind.
            Reimplemented by country packages
        """
        return test_case

    def post_process_test_case(self, test_case, period, state):
        """
            Country package custom treatment applied to the test case after the commons ones.
            Reimplemented by country packages
        """
        return test_case, None


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
                                period = conv.function(periods.period),
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
                    conv.not_none,
                    ),
                conv.noop,
                ),
            )(value, state = state)

        if errors is not None:
            return input_variables, errors

        for input_variable_name in input_variables.keys():
            if input_variable_name not in variables_name:
                # We only import VariableNotFound here to avoid a circular dependency in imports
                from .taxbenefitsystems import VariableNotFound
                raise VariableNotFound(input_variable_name, tax_benefit_system)

        input_variables, errors = conv.pipe(
            make_json_or_python_to_array_by_period_by_variable_name(tax_benefit_system, period),
            conv.empty_to_none,
            )(value, state = state)
        if errors is not None:
            return input_variables, errors
        if input_variables is None:
            return input_variables, None

        count_by_entity_key = {}
        errors = {}
        for variable_name, array_by_period in input_variables.iteritems():
            column = tax_benefit_system.get_column(variable_name)
            entity_key = column.entity.key
            entity_count = count_by_entity_key.get(entity_key, 0)
            for variable_period, variable_array in array_by_period.iteritems():
                if entity_count == 0:
                    count_by_entity_key[entity_key] = entity_count = len(variable_array)
                elif len(variable_array) != entity_count:
                    errors[column.name] = state._(
                        u"Array has not the same length as other variables of entity {}: {} instead of {}").format(
                            column.name, len(variable_array), entity_count)

        return input_variables, errors or None

    return json_or_python_to_input_variables


def make_json_or_python_to_test(tax_benefit_system):
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
                input_variables = conv.pipe(
                    conv.test_isinstance(dict),
                    conv.uniform_mapping(
                        conv.pipe(
                            conv.test_isinstance(basestring),
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
                    conv.function(periods.period),
                    conv.not_none,
                    ),
                relative_error_margin = conv.pipe(
                    conv.test_isinstance((float, int)),
                    conv.test_greater_or_equal(0),
                    ),
                ).iteritems(),
            (
                (entity.plural, conv.pipe(
                    conv.make_item_to_singleton(),
                    conv.test_isinstance(list),
                    ))
                for entity in tax_benefit_system.entities
                ),
            )),
        )

    def json_or_python_to_test(value, state = None):
        if value is None:
            return value, None
        if state is None:
            state = conv.default_state
        value, error = conv.pipe(
            conv.test_isinstance(dict),
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
        input_variables = test_case.pop(u'input_variables')
        keywords = test_case.pop(u'keywords')
        name = test_case.pop(u'name')
        output_variables = test_case.pop(u'output_variables')
        period = test_case.pop(u'period')
        relative_error_margin = test_case.pop(u'relative_error_margin')

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
                keywords = keywords,
                name = name,
                output_variables = output_variables,
                relative_error_margin = relative_error_margin,
                scenario = scenario,
                ).iteritems()
            if value is not None
            }, None

    return json_or_python_to_test


def iter_over_entity_members(entity_description, scenario_entity):
        # One by one, yield individu_role, individy_legacy_role, individu_id
        legacy_role_i = 0
        for role in entity_description.roles:
            role_name = role.plural or role.key
            individus = scenario_entity[role_name]

            if individus:
                if not type(individus) == list:
                    individus = [individus]

                legacy_role_j = 0
                for individu in individus:
                    if role.subroles:
                        yield role.subroles[legacy_role_j], legacy_role_i + legacy_role_j, individu
                    else:
                        yield role, legacy_role_i + legacy_role_j, individu
                    legacy_role_j += 1
            legacy_role_i += (role.max or 1)
