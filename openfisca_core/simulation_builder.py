# -*- coding: utf-8 -*-
from typing import Dict, List, Iterable

import dpath
import numpy as np
from copy import deepcopy

from openfisca_core.entities import Entity
from openfisca_core.populations import Population
from openfisca_core.variables import Variable

from openfisca_core.errors import VariableNotFound, SituationParsingError, PeriodMismatchError
from openfisca_core.periods import period, key_period_size
from openfisca_core.simulations import Simulation


class SimulationBuilder(object):

    def __init__(self):
        self.default_period = None  # Simulation period used for variables when no period is defined
        self.persons_plural = None  # Plural name for person entity in current tax and benefits system

        # JSON input - Memory of known input values. Indexed by variable or axis name.
        self.input_buffer: Dict[Variable.name, Dict[str(period), np.array]] = {}
        self.populations: Dict[Entity.key, Population] = {}
        # JSON input - Number of items of each entity type. Indexed by entities plural names. Should be consistent with ``entity_ids``, including axes.
        self.entity_counts: Dict[Entity.plural, int] = {}
        # JSON input - List of items of each entity type. Indexed by entities plural names. Should be consistent with ``entity_counts``.
        self.entity_ids: Dict[Entity.plural, List[int]] = {}

        # Links entities with persons. For each person index in persons ids list, set entity index in entity ids id. E.g.: self.memberships[entity.plural][person_index] = entity_ids.index(instance_id)
        self.memberships: Dict[Entity.plural, List[int]] = {}
        self.roles: Dict[Entity.plural, List[int]] = {}

        self.variable_entities: Dict[Variable.name, Entity] = {}

        self.axes = [[]]
        self.axes_entity_counts: Dict[Entity.plural, int] = {}
        self.axes_entity_ids: Dict[Entity.plural, List[int]] = {}
        self.axes_memberships: Dict[Entity.plural, List[int]] = {}
        self.axes_roles: Dict[Entity.plural, List[int]] = {}

    def build_from_dict(self, tax_benefit_system, input_dict):
        """
            Build a simulation from ``input_dict``

            This method uses :any:`build_from_entities` if entities are fully specified, or :any:`build_from_variables` if not.

            :param dict input_dict: A dict represeting the input of the simulation
            :return: A :any:`Simulation`
        """

        input_dict = self.explicit_singular_entities(tax_benefit_system, input_dict)
        if any(key in tax_benefit_system.entities_plural() for key in input_dict.keys()):
            return self.build_from_entities(tax_benefit_system, input_dict)
        else:
            return self.build_from_variables(tax_benefit_system, input_dict)

    def build_from_entities(self, tax_benefit_system, input_dict):
        """
            Build a simulation from a Python dict ``input_dict`` fully specifying entities.

            Examples:

            >>> simulation_builder.build_from_entities({
                'persons': {'Javier': { 'salary': {'2018-11': 2000}}},
                'households': {'household': {'parents': ['Javier']}}
                })
        """
        input_dict = deepcopy(input_dict)

        simulation = Simulation(tax_benefit_system, tax_benefit_system.instantiate_entities())

        # Register variables so get_variable_entity can find them
        for (variable_name, _variable) in tax_benefit_system.variables.items():
            self.register_variable(variable_name, simulation.get_variable_population(variable_name).entity)

        check_type(input_dict, dict, ['error'])
        axes = input_dict.pop('axes', None)

        unexpected_entities = [entity for entity in input_dict if entity not in tax_benefit_system.entities_plural()]
        if unexpected_entities:
            unexpected_entity = unexpected_entities[0]
            raise SituationParsingError([unexpected_entity],
                ''.join([
                    "Some entities in the situation are not defined in the loaded tax and benefit system.",
                    "These entities are not found: {0}.",
                    "The defined entities are: {1}."]
                    )
                .format(
                ', '.join(unexpected_entities),
                ', '.join(tax_benefit_system.entities_plural())
                    )
                )
        persons_json = input_dict.get(tax_benefit_system.person_entity.plural, None)

        if not persons_json:
            raise SituationParsingError([tax_benefit_system.person_entity.plural],
                'No {0} found. At least one {0} must be defined to run a simulation.'.format(tax_benefit_system.person_entity.key))

        persons_ids = self.add_person_entity(simulation.persons.entity, persons_json)

        for entity_class in tax_benefit_system.group_entities:
            instances_json = input_dict.get(entity_class.plural)
            if instances_json is not None:
                self.add_group_entity(self.persons_plural, persons_ids, entity_class, instances_json)
            else:
                self.add_default_group_entity(persons_ids, entity_class)

        if axes:
            self.axes = axes
            self.expand_axes()

        try:
            self.finalize_variables_init(simulation.persons)
        except PeriodMismatchError as e:
            self.raise_period_mismatch(simulation.persons.entity, persons_json, e)

        for entity_class in tax_benefit_system.group_entities:
            try:
                population = simulation.populations[entity_class.key]
                self.finalize_variables_init(population)
            except PeriodMismatchError as e:
                self.raise_period_mismatch(population.entity, instances_json, e)

        return simulation

    def build_from_variables(self, tax_benefit_system, input_dict):
        """
            Build a simulation from a Python dict ``input_dict`` describing variables values without expliciting entities.

            This method uses :any:`build_default_simulation` to infer an entity structure

            Example:

            >>> simulation_builder.build_from_variables(
                {'salary': {'2016-10': 12000}}
                )
        """
        count = _get_person_count(input_dict)
        simulation = self.build_default_simulation(tax_benefit_system, count)
        for variable, value in input_dict.items():
            if not isinstance(value, dict):
                if self.default_period is None:
                    raise SituationParsingError([variable],
                        "Can't deal with type: expected object. Input variables should be set for specific periods. For instance: {'salary': {'2017-01': 2000, '2017-02': 2500}}, or {'birth_date': {'ETERNITY': '1980-01-01'}}.")
                simulation.set_input(variable, self.default_period, value)
            else:
                for period_str, dated_value in value.items():
                    simulation.set_input(variable, period_str, dated_value)
        return simulation

    def build_default_simulation(self, tax_benefit_system, count = 1):
        """
            Build a simulation where:
                - There are ``count`` persons
                - There are ``count`` instances of each group entity, containing one person
                - Every person has, in each entity, the first role
        """

        simulation = Simulation(tax_benefit_system, tax_benefit_system.instantiate_entities())
        for population in simulation.populations.values():
            population.count = count
            population.ids = np.array(range(count))
            if not population.entity.is_person:
                population.members_entity_id = population.ids  # Each person is its own group entity
        return simulation

    def create_entities(self, tax_benefit_system):
        self.populations = tax_benefit_system.instantiate_entities()

    def declare_person_entity(self, person_singular, persons_ids: Iterable):
        person_instance = self.populations[person_singular]
        person_instance.ids = np.array(list(persons_ids))
        person_instance.count = len(person_instance.ids)

        self.persons_plural = person_instance.entity.plural

    def declare_entity(self, entity_singular, entity_ids: Iterable):
        entity_instance = self.populations[entity_singular]
        entity_instance.ids = np.array(list(entity_ids))
        entity_instance.count = len(entity_instance.ids)
        return entity_instance

    def nb_persons(self, entity_singular, role = None):
        return self.populations[entity_singular].nb_persons(role = role)

    def join_with_persons(self, group_population, persons_group_assignment, roles: Iterable[str]):
        # Maps group's identifiers to a 0-based integer range, for indexing into members_roles (see PR#876)
        group_sorted_indices = np.unique(persons_group_assignment, return_inverse = True)[1]
        group_population.members_entity_id = np.argsort(group_population.ids)[group_sorted_indices]

        flattened_roles = group_population.entity.flattened_roles
        roles_array = np.array(roles)
        if np.issubdtype(roles_array.dtype, np.integer):
            group_population.members_role = np.array(flattened_roles)[roles_array]
        else:
            group_population.members_role = np.select([roles_array == role.key for role in flattened_roles], flattened_roles)

    def build(self, tax_benefit_system):
        return Simulation(tax_benefit_system, self.populations)

    def explicit_singular_entities(self, tax_benefit_system, input_dict):
        """
            Preprocess ``input_dict`` to explicit entities defined using the single-entity shortcut

            Example:

            >>> simulation_builder.explicit_singular_entities(
                {'persons': {'Javier': {}, }, 'household': {'parents': ['Javier']}}
                )
            >>> {'persons': {'Javier': {}}, 'households': {'household': {'parents': ['Javier']}}
        """

        singular_keys = set(input_dict).intersection(tax_benefit_system.entities_by_singular())
        if not singular_keys:
            return input_dict

        result = {
            entity_id: entity_description
            for (entity_id, entity_description) in input_dict.items()
            if entity_id in tax_benefit_system.entities_plural()
            }  # filter out the singular entities

        for singular in singular_keys:
            plural = tax_benefit_system.entities_by_singular()[singular].plural
            result[plural] = {singular: input_dict[singular]}

        return result

    def add_person_entity(self, entity, instances_json):
        """
            Add the simulation's instances of the persons entity as described in ``instances_json``.
        """
        check_type(instances_json, dict, [entity.plural])
        entity_ids = list(map(str, instances_json.keys()))
        self.persons_plural = entity.plural
        self.entity_ids[self.persons_plural] = entity_ids
        self.entity_counts[self.persons_plural] = len(entity_ids)

        for instance_id, instance_object in instances_json.items():
            check_type(instance_object, dict, [entity.plural, instance_id])
            self.init_variable_values(entity, instance_object, str(instance_id))

        return self.get_ids(entity.plural)

    def add_default_group_entity(self, persons_ids, entity):
        persons_count = len(persons_ids)
        self.entity_ids[entity.plural] = persons_ids
        self.entity_counts[entity.plural] = persons_count
        self.memberships[entity.plural] = np.arange(0, persons_count, dtype = np.int32)
        self.roles[entity.plural] = np.repeat(entity.flattened_roles[0], persons_count)

    def add_group_entity(self, persons_plural, persons_ids, entity, instances_json):
        """
            Add all instances of one of the model's entities as described in ``instances_json``.
        """
        check_type(instances_json, dict, [entity.plural])
        entity_ids = list(map(str, instances_json.keys()))

        self.entity_ids[entity.plural] = entity_ids
        self.entity_counts[entity.plural] = len(entity_ids)

        persons_count = len(persons_ids)
        persons_to_allocate = set(persons_ids)
        self.memberships[entity.plural] = np.empty(persons_count, dtype = np.int32)
        self.roles[entity.plural] = np.empty(persons_count, dtype = object)

        self.entity_ids[entity.plural] = entity_ids
        self.entity_counts[entity.plural] = len(entity_ids)

        for instance_id, instance_object in instances_json.items():
            check_type(instance_object, dict, [entity.plural, instance_id])

            variables_json = instance_object.copy()  # Don't mutate function input

            roles_json = {
                role.plural or role.key: transform_to_strict_syntax(variables_json.pop(role.plural or role.key, []))
                for role in entity.roles
                }

            for role_id, role_definition in roles_json.items():
                check_type(role_definition, list, [entity.plural, instance_id, role_id])
                for index, person_id in enumerate(role_definition):
                    entity_plural = entity.plural
                    self.check_persons_to_allocate(persons_plural, entity_plural,
                                                   persons_ids,
                                                   person_id, instance_id, role_id,
                                                   persons_to_allocate, index)

                    persons_to_allocate.discard(person_id)

            entity_index = entity_ids.index(instance_id)
            role_by_plural = {role.plural or role.key: role for role in entity.roles}

            for role_plural, persons_with_role in roles_json.items():
                role = role_by_plural[role_plural]

                if role.max is not None and len(persons_with_role) > role.max:
                    raise SituationParsingError([entity.plural, instance_id, role_plural], f"There can be at most {role.max} {role_plural} in a {entity.key}. {len(persons_with_role)} were declared in '{instance_id}'.")

                for index_within_role, person_id in enumerate(persons_with_role):
                    person_index = persons_ids.index(person_id)
                    self.memberships[entity.plural][person_index] = entity_index
                    person_role = role.subroles[index_within_role] if role.subroles else role
                    self.roles[entity.plural][person_index] = person_role

            self.init_variable_values(entity, variables_json, instance_id)

        if persons_to_allocate:
            entity_ids = entity_ids + list(persons_to_allocate)
            for person_id in persons_to_allocate:
                person_index = persons_ids.index(person_id)
                self.memberships[entity.plural][person_index] = entity_ids.index(person_id)
                self.roles[entity.plural][person_index] = entity.flattened_roles[0]
            # Adjust previously computed ids and counts
            self.entity_ids[entity.plural] = entity_ids
            self.entity_counts[entity.plural] = len(entity_ids)

        # Convert back to Python array
        self.roles[entity.plural] = self.roles[entity.plural].tolist()
        self.memberships[entity.plural] = self.memberships[entity.plural].tolist()

    def set_default_period(self, period_str):
        if period_str:
            self.default_period = str(period(period_str))

    def get_input(self, variable, period_str):
        if variable not in self.input_buffer:
            self.input_buffer[variable] = {}
        return self.input_buffer[variable].get(period_str)

    def check_persons_to_allocate(self, persons_plural, entity_plural,
                                  persons_ids,
                                  person_id, entity_id, role_id,
                                  persons_to_allocate, index):
        check_type(person_id, str, [entity_plural, entity_id, role_id, str(index)])
        if person_id not in persons_ids:
            raise SituationParsingError([entity_plural, entity_id, role_id],
                "Unexpected value: {0}. {0} has been declared in {1} {2}, but has not been declared in {3}.".format(
                    person_id, entity_id, role_id, persons_plural)
                )
        if person_id not in persons_to_allocate:
            raise SituationParsingError([entity_plural, entity_id, role_id],
                "{} has been declared more than once in {}".format(
                    person_id, entity_plural)
                )

    def init_variable_values(self, entity, instance_object, instance_id):
        for variable_name, variable_values in instance_object.items():
            path_in_json = [entity.plural, instance_id, variable_name]
            try:
                entity.check_variable_defined_for_entity(variable_name)
            except ValueError as e:  # The variable is defined for another entity
                raise SituationParsingError(path_in_json, e.args[0])
            except VariableNotFound as e:  # The variable doesn't exist
                raise SituationParsingError(path_in_json, str(e), code = 404)

            instance_index = self.get_ids(entity.plural).index(instance_id)

            if not isinstance(variable_values, dict):
                if self.default_period is None:
                    raise SituationParsingError(path_in_json,
                        "Can't deal with type: expected object. Input variables should be set for specific periods. For instance: {'salary': {'2017-01': 2000, '2017-02': 2500}}, or {'birth_date': {'ETERNITY': '1980-01-01'}}.")
                variable_values = {self.default_period: variable_values}

            for period_str, value in variable_values.items():
                try:
                    period(period_str)
                except ValueError as e:
                    raise SituationParsingError(path_in_json, e.args[0])
                variable = entity.get_variable(variable_name)
                self.add_variable_value(entity, variable, instance_index, instance_id, period_str, value)

    def add_variable_value(self, entity, variable, instance_index, instance_id, period_str, value):
        path_in_json = [entity.plural, instance_id, variable.name, period_str]

        if value is None:
            return

        array = self.get_input(variable.name, str(period_str))

        if array is None:
            array_size = self.get_count(entity.plural)
            array = variable.default_array(array_size)

        try:
            value = variable.check_set_value(value)
        except ValueError as error:
            raise SituationParsingError(path_in_json, *error.args)

        array[instance_index] = value

        self.input_buffer[variable.name][str(period(period_str))] = array

    def finalize_variables_init(self, population):
        # Due to set_input mechanism, we must bufferize all inputs, then actually set them,
        # so that the months are set first and the years last.
        plural_key = population.entity.plural
        if plural_key in self.entity_counts:
            population.count = self.get_count(plural_key)
            population.ids = self.get_ids(plural_key)
        if plural_key in self.memberships:
            population.members_entity_id = np.array(self.get_memberships(plural_key))
            population.members_role = np.array(self.get_roles(plural_key))
        for variable_name in self.input_buffer.keys():
            try:
                holder = population.get_holder(variable_name)
            except ValueError:  # Wrong entity, we can just ignore that
                continue
            buffer = self.input_buffer[variable_name]
            periods = [period(period_str) for period_str in self.input_buffer[variable_name].keys()]
            # We need to handle small periods first for set_input to work
            sorted_periods = sorted(periods, key=key_period_size)
            for period_value in sorted_periods:
                values = buffer[str(period_value)]
                # Hack to replicate the values in the persons entity
                # when we have an axis along a group entity but not persons
                array = np.tile(values, population.count // len(values))
                variable = holder.variable
                # TODO - this duplicates the check in Simulation.set_input, but
                # fixing that requires improving Simulation's handling of entities
                if (variable.end is None) or (period_value.start.date <= variable.end):
                    holder.set_input(period_value, array)

    def raise_period_mismatch(self, entity, json, e):
        # This error happens when we try to set a variable value for a period that doesn't match its definition period
        # It is only raised when we consume the buffer. We thus don't know which exact key caused the error.
        # We do a basic research to find the culprit path
        culprit_path = next(
            dpath.search(json, "*/{}/{}".format(e.variable_name, str(e.period)), yielded = True),
            None)
        if culprit_path:
            path = [entity.plural] + culprit_path[0].split('/')
        else:
            path = [entity.plural]  # Fallback: if we can't find the culprit, just set the error at the entities level

        raise SituationParsingError(path, e.message)

    # Returns the total number of instances of this entity, including when there is replication along axes
    def get_count(self, entity_name):
        return self.axes_entity_counts.get(entity_name, self.entity_counts[entity_name])

    # Returns the ids of instances of this entity, including when there is replication along axes
    def get_ids(self, entity_name):
        return self.axes_entity_ids.get(entity_name, self.entity_ids[entity_name])

    # Returns the memberships of individuals in this entity, including when there is replication along axes
    def get_memberships(self, entity_name):
        # Return empty array for the "persons" entity
        return self.axes_memberships.get(entity_name, self.memberships.get(entity_name, []))

    # Returns the roles of individuals in this entity, including when there is replication along axes
    def get_roles(self, entity_name):
        # Return empty array for the "persons" entity
        return self.axes_roles.get(entity_name, self.roles.get(entity_name, []))

    def add_parallel_axis(self, axis):
        # All parallel axes have the same count and entity.
        # Search for a compatible axis, if none exists, error out
        self.axes[0].append(axis)

    def add_perpendicular_axis(self, axis):
        # This adds an axis perpendicular to all previous dimensions
        self.axes.append([axis])

    def expand_axes(self):
        # This method should be idempotent & allow change in axes
        perpendicular_dimensions = self.axes

        cell_count = 1
        for parallel_axes in perpendicular_dimensions:
            first_axis = parallel_axes[0]
            axis_count = first_axis['count']
            cell_count *= axis_count

        # Scale the "prototype" situation, repeating it cell_count times
        for entity_name in self.entity_counts.keys():
            # Adjust counts
            self.axes_entity_counts[entity_name] = self.get_count(entity_name) * cell_count
            # Adjust ids
            original_ids = self.get_ids(entity_name) * cell_count
            indices = np.arange(0, cell_count * self.entity_counts[entity_name])
            adjusted_ids = [id + str(ix) for id, ix in zip(original_ids, indices)]
            self.axes_entity_ids[entity_name] = adjusted_ids
            # Adjust roles
            original_roles = self.get_roles(entity_name)
            adjusted_roles = original_roles * cell_count
            self.axes_roles[entity_name] = adjusted_roles
            # Adjust memberships, for group entities only
            if entity_name != self.persons_plural:
                original_memberships = self.get_memberships(entity_name)
                repeated_memberships = original_memberships * cell_count
                indices = np.repeat(np.arange(0, cell_count), len(original_memberships)) * self.entity_counts[entity_name]
                adjusted_memberships = (np.array(repeated_memberships) + indices).tolist()
                self.axes_memberships[entity_name] = adjusted_memberships

        # Now generate input values along the specified axes
        # TODO - factor out the common logic here
        if len(self.axes) == 1 and len(self.axes[0]):
            parallel_axes = self.axes[0]
            first_axis = parallel_axes[0]
            axis_count: int = first_axis['count']
            axis_entity = self.get_variable_entity(first_axis['name'])
            axis_entity_step_size = self.entity_counts[axis_entity.plural]
            # Distribute values along axes
            for axis in parallel_axes:
                axis_index = axis.get('index', 0)
                axis_period = axis.get('period', self.default_period)
                axis_name = axis['name']
                variable = axis_entity.get_variable(axis_name)
                array = self.get_input(axis_name, axis_period)
                if array is None:
                    array = variable.default_array(axis_count * axis_entity_step_size)
                array[axis_index:: axis_entity_step_size] = np.linspace(
                    axis['min'],
                    axis['max'],
                    num = axis_count,
                    )
                # Set input
                self.input_buffer[axis_name][str(axis_period)] = array
        else:
            first_axes_count: List[int] = (
                parallel_axes[0]["count"]
                for parallel_axes
                in self.axes
                )
            axes_linspaces = [
                np.linspace(0, axis_count - 1, num = axis_count)
                for axis_count
                in first_axes_count
                ]
            axes_meshes = np.meshgrid(*axes_linspaces)
            for parallel_axes, mesh in zip(self.axes, axes_meshes):
                first_axis = parallel_axes[0]
                axis_count = first_axis['count']
                axis_entity = self.get_variable_entity(first_axis['name'])
                axis_entity_step_size = self.entity_counts[axis_entity.plural]
                # Distribute values along the grid
                for axis in parallel_axes:
                    axis_index = axis.get('index', 0)
                    axis_period = axis['period'] or self.default_period
                    axis_name = axis['name']
                    variable = axis_entity.get_variable(axis_name)
                    array = self.get_input(axis_name, axis_period)
                    if array is None:
                        array = variable.default_array(cell_count * axis_entity_step_size)
                    array[axis_index:: axis_entity_step_size] = axis['min'] \
                        + mesh.reshape(cell_count) * (axis['max'] - axis['min']) / (axis_count - 1)
                    self.input_buffer[axis_name][str(axis_period)] = array

    def get_variable_entity(self, variable_name):
        return self.variable_entities[variable_name]

    def register_variable(self, variable_name, entity):
        self.variable_entities[variable_name] = entity


def check_type(input, input_type, path = None):
    json_type_map = {
        dict: "Object",
        list: "Array",
        str: "String",
        }

    if path is None:
        path = []

    if not isinstance(input, input_type):
        raise SituationParsingError(path,
            "Invalid type: must be of type '{}'.".format(json_type_map[input_type]))


def transform_to_strict_syntax(data):
    if isinstance(data, (str, int)):
        data = [data]
    if isinstance(data, list):
        return [str(item) if isinstance(item, int) else item for item in data]
    return data


def _get_person_count(input_dict):
    try:
        first_value = next(iter(input_dict.values()))
        if isinstance(first_value, dict):
            first_value = next(iter(first_value.values()))
        if isinstance(first_value, str):
            return 1

        return len(first_value)
    except Exception:
        return 1
