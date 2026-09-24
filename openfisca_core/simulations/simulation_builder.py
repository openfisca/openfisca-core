from __future__ import annotations

from collections.abc import Iterable, Sequence
from numpy.typing import NDArray as Array
from typing import NoReturn

import copy

import dpath
import numpy

from openfisca_core import entities, errors, periods, populations, variables

from . import helpers
from ._build_default_simulation import _BuildDefaultSimulation
from ._build_from_variables import _BuildFromVariables
from ._type_guards import (
    are_entities_fully_specified,
    are_entities_short_form,
    are_entities_specified,
    has_axes,
)
from .simulation import Simulation
from .typing import (
    Axis,
    Entity,
    FullySpecifiedEntities,
    GroupEntities,
    ImplicitGroupEntities,
    Params,
    ParamsWithoutAxes,
    Population,
    Role,
    TaxBenefitSystem,
    Variables,
)


class SimulationBuilder:
    def __init__(self) -> None:
        self.default_period = (
            None  # Simulation period used for variables when no period is defined
        )
        # JSON input - Memory of known input values. Indexed by variable or axis name.
        self.input_buffer: dict[
            variables.Variable.name,
            dict[str(periods.period), numpy.array],
        ] = {}
        self.populations: dict[entities.Entity.key, populations.Population] = {}

        # JSON input - Number of items of each entity type. Indexed by entities key names. Should be consistent with ``entity_ids``, including axes.
        self.entity_counts: dict[entities.Entity.key, int] = {}
        # JSON input - List of items of each entity type. Indexed by entities key names. Should be consistent with ``entity_counts``.
        self.entity_ids: dict[entities.Entity.key, list[int]] = {}

        # Links entities together
        self.memberships: dict[entities.Relationship.name, list[int]] = {}
        self.roles: dict[entities.Relationship, list[int]] = {}

        self.variable_entities: dict[variables.Variable.name, entities.Entity] = {}

        self.axes = [[]]
        self.axes_entity_counts: dict[entities.Entity.key, int] = {}
        self.axes_entity_ids: dict[entities.Entity.key, list[int]] = {}
        self.axes_memberships: dict[entities.Relationship.name, list[int]] = {}
        self.axes_roles: dict[entities.Relationship.name, list[int]] = {}
        self.axes_entity_map: dict[entities.Entity.key, entities.Entity] = {}

    def build_from_dict(
        self,
        tax_benefit_system: TaxBenefitSystem,
        input_dict: Params,
    ) -> Simulation:
        """Build a simulation from an input dictionary.

        This method uses :meth:`.SimulationBuilder.build_from_entities` if
        entities are fully specified, or
        :meth:`.SimulationBuilder.build_from_variables` if they are not.

        Args:
            tax_benefit_system: The system to use.
            input_dict: The input of the simulation.

        Returns:
            Simulation: The built simulation.

        Examples:
            >>> entities = {"person", "household"}

            >>> params = {
            ...     "persons": {"Javier": {"salary": {"2018-11": 2000}}},
            ...     "household": {"parents": ["Javier"]},
            ...     "axes": [[{"count": 1, "max": 1, "min": 1, "name": "household"}]],
            ... }

            >>> are_entities_short_form(params, entities)
            True

            >>> entities = {"persons", "households"}

            >>> params = {
            ...     "axes": [
            ...         [
            ...             {
            ...                 "count": 2,
            ...                 "max": 3000,
            ...                 "min": 0,
            ...                 "name": "rent",
            ...                 "period": "2018-11",
            ...             }
            ...         ]
            ...     ],
            ...     "households": {
            ...         "housea": {"parents": ["Alicia", "Javier"]},
            ...         "houseb": {"parents": ["Tom"]},
            ...     },
            ...     "persons": {
            ...         "Alicia": {"salary": {"2018-11": 0}},
            ...         "Javier": {},
            ...         "Tom": {},
            ...     },
            ... }

            >>> are_entities_short_form(params, entities)
            True

            >>> params = {"salary": [12000, 13000]}

            >>> not are_entities_specified(params, {"salary"})
            True

        """
        #: The plural names of the entities in the tax and benefits system.
        plural: Iterable[str] = tax_benefit_system.entities_plural()

        #: The singular names of the entities in the tax and benefits system.
        singular: Iterable[str] = tax_benefit_system.entities_by_singular()

        #: The names of the variables in the tax and benefits system.
        variables: Iterable[str] = tax_benefit_system.variables.keys()

        if are_entities_short_form(input_dict, singular):
            params = self.explicit_singular_entities(tax_benefit_system, input_dict)
            return self.build_from_entities(tax_benefit_system, params)

        if are_entities_fully_specified(params := input_dict, plural):
            return self.build_from_entities(tax_benefit_system, params)

        if not are_entities_specified(params := input_dict, variables):
            return self.build_from_variables(tax_benefit_system, params)
        return None

    def build_from_entities(
        self,
        tax_benefit_system: TaxBenefitSystem,
        input_dict: FullySpecifiedEntities,
    ) -> Simulation:
        """Build a simulation from a Python dict ``input_dict`` fully specifying
        entities.

        Examples:
            >>> entities = {"person", "household"}

            >>> params = {
            ...     "persons": {"Javier": {"salary": {"2018-11": 2000}}},
            ...     "household": {"parents": ["Javier"]},
            ...     "axes": [[{"count": 1, "max": 1, "min": 1, "name": "household"}]],
            ... }

            >>> are_entities_short_form(params, entities)
            True

        """
        # Create the populations
        populations = tax_benefit_system.instantiate_entities()

        # Create the simulation
        simulation = Simulation(tax_benefit_system, populations)

        # Why?
        input_dict = copy.deepcopy(input_dict)

        # The plural names of the entities in the tax and benefits system.
        plural: Iterable[str] = tax_benefit_system.entities_plural()

        # Register variables so get_variable_entity can find them
        self.register_variables(simulation)

        # Declare axes
        axes: list[list[Axis]] | None = None

        # ?
        helpers.check_type(input_dict, dict, ["error"])

        # Remove axes from input_dict
        params: ParamsWithoutAxes = {
            key: value for key, value in input_dict.items() if key != "axes"
        }

        # Save axes for later
        if has_axes(axes_params := input_dict):
            axes = copy.deepcopy(axes_params.get("axes", None))

        # Check for unexpected entities
        helpers.check_unexpected_entities(params, plural)

        for entity_class in tax_benefit_system.entities:
            instances_json = params.get(entity_class.plural)
            self.add_entity(entity_class, instances_json or {})

        for entity_class in tax_benefit_system.entities:
            instances_json = params.get(entity_class.plural)
            self.link_entities(entity_class, instances_json or {})

        self.save_memberships(simulation)

        if axes is not None:
            for axis in axes[0]:
                self.add_parallel_axis(axis)

            if len(axes) >= 1:
                for axis in axes[1:]:
                    self.add_perpendicular_axis(axis[0])

            self.expand_axes()

        for entity_class in tax_benefit_system.entities:
            try:
                population = simulation.populations[entity_class.key]
                self.finalize_variables_init(population)
            except errors.PeriodMismatchError as e:
                instances_json = params.get(entity_class.plural)
                self.raise_period_mismatch(population.entity, instances_json, e)

        return simulation

    def build_from_variables(
        self,
        tax_benefit_system: TaxBenefitSystem,
        input_dict: Variables,
    ) -> Simulation:
        """Build a simulation from a Python dict ``input_dict`` describing
        variables values without expliciting entities.

        This method uses :meth:`.SimulationBuilder.build_default_simulation` to
        infer an entity structure.

        Args:
            tax_benefit_system: The system to use.
            input_dict: The input of the simulation.

        Returns:
            Simulation: The built simulation.

        Raises:
            SituationParsingError: If the input is not valid.

        Examples:
            >>> params = {"salary": {"2016-10": 12000}}

            >>> are_entities_specified(params, {"salary"})
            False

            >>> params = {"salary": 12000}

            >>> are_entities_specified(params, {"salary"})
            False

        """
        return (
            _BuildFromVariables(tax_benefit_system, input_dict, self.default_period)
            .add_dated_values()
            .add_undated_values()
            .simulation
        )

    @staticmethod
    def build_default_simulation(
        tax_benefit_system: TaxBenefitSystem,
        count: int = 1,
    ) -> Simulation:
        """Build a default simulation.

        Where:
            - There are ``count`` persons
            - There are ``count`` of each group entity, containing one person
            - Every person has, in each entity, the first role

        """
        return (
            _BuildDefaultSimulation(tax_benefit_system, count)
            .add_count()
            .add_ids()
            .add_members_entity_id()
            .simulation
        )

    def create_entities(self, tax_benefit_system) -> None:
        self.populations = tax_benefit_system.instantiate_entities()

    def declare_entity(self, entity_singular, entity_ids: Iterable):
        entity_instance = self.populations[entity_singular]
        entity_instance.ids = numpy.array(list(entity_ids))
        entity_instance.count = len(entity_instance.ids)
        return entity_instance

    def nb_persons(self, entity_singular, role=None):
        return self.populations[entity_singular].nb_persons(role=role)

    def join(
        self,
        group_population,
        members_population,
        persons_group_assignment,
        roles: Iterable[str],
    ) -> None:
        # Determine membership
        membership = group_population.single_membership

        # Maps group's identifiers to a 0-based integer range, for indexing into members_roles (see PR#876)
        group_sorted_indices = numpy.unique(
            persons_group_assignment,
            return_inverse=True,
        )[1]
        membership.members_entity_id = numpy.argsort(group_population.ids)[
            group_sorted_indices
        ]

        flattened_roles = group_population.entity.flattened_roles
        roles_array = numpy.array(roles)
        if numpy.issubdtype(roles_array.dtype, numpy.integer):
            membership.members_role = numpy.array(flattened_roles)[roles_array]
        elif len(flattened_roles) == 0:
            membership.members_role = numpy.int16(0)
        else:
            membership.members_role = numpy.select(
                [roles_array == role.key for role in flattened_roles],
                flattened_roles,
            )

    def build(self, tax_benefit_system):
        return Simulation(tax_benefit_system, self.populations)

    def explicit_singular_entities(
        self,
        tax_benefit_system: TaxBenefitSystem,
        input_dict: ImplicitGroupEntities,
    ) -> GroupEntities:
        """Preprocess ``input_dict`` to explicit entities defined using the
        single-entity shortcut.

        Examples:
            >>> params = {
            ...     "persons": {
            ...         "Javier": {},
            ...     },
            ...     "household": {"parents": ["Javier"]},
            ... }

            >>> are_entities_fully_specified(params, {"persons", "households"})
            False

            >>> are_entities_short_form(params, {"person", "household"})
            True

            >>> params = {
            ...     "persons": {"Javier": {}},
            ...     "households": {"household": {"parents": ["Javier"]}},
            ... }

            >>> are_entities_fully_specified(params, {"persons", "households"})
            True

            >>> are_entities_short_form(params, {"person", "household"})
            False

        """
        singular_keys = set(input_dict).intersection(
            tax_benefit_system.entities_by_singular(),
        )

        result = {
            entity_id: entity_description
            for (entity_id, entity_description) in input_dict.items()
            if entity_id in tax_benefit_system.entities_plural()
        }  # filter out the singular entities

        for singular in singular_keys:
            plural = tax_benefit_system.entities_by_singular()[singular].plural
            result[plural] = {singular: input_dict[singular]}

        return result

    def add_entity(self, entity: Entity, instances_json):
        """Add the simulation's instances of the entity as described in ``instances_json``."""
        helpers.check_type(instances_json, dict, [entity.plural])
        entity_ids = list(map(str, instances_json.keys()))
        self.entity_ids[entity.key] = entity_ids
        self.entity_counts[entity.key] = len(entity_ids)
        self.axes_entity_map[entity.key] = entity

        for instance_id, instance_object in instances_json.items():
            helpers.check_type(instance_object, dict, [entity.plural, instance_id])
            self.init_variable_values(entity, instance_object, str(instance_id))

        return self.get_ids(entity.key)

    def link_entities(
        self,
        entity: Entity,
        instances_json,
    ) -> None:
        """Add all instances of one of the model's entities as described in ``instances_json``."""
        for relationship in entity.relationships:
            if relationship.a.key != entity.key:
                continue

            members = relationship.b
            members_ids = self.get_ids(members.key)
            members_count = len(members_ids)
            members_to_allocate = set(members_ids)

            membership_array = numpy.empty(members_count, dtype=numpy.int32)
            roles = numpy.empty(members_count, dtype=object)

            entity_ids = self.get_ids(entity.key)

            for instance_id, instance_object in instances_json.items():
                helpers.check_type(instance_object, dict, [entity.plural, instance_id])

                variables_json = instance_object.copy()  # Don't mutate function input

                roles_json = {
                    role.plural
                    or role.key: helpers.transform_to_strict_syntax(
                        variables_json.pop(role.plural or role.key, []),
                    )
                    for role in relationship.roles
                }

                for role_id, role_definition in roles_json.items():
                    helpers.check_type(
                        role_definition,
                        list,
                        [entity.plural, instance_id, role_id],
                    )
                    for index, member_id in enumerate(role_definition):
                        entity_plural = entity.plural
                        self.check_members_to_allocate(
                            members.plural,
                            entity_plural,
                            members_ids,
                            member_id,
                            instance_id,
                            role_id,
                            members_to_allocate,
                            index,
                        )

                        members_to_allocate.discard(member_id)

                entity_index = entity_ids.index(instance_id)
                role_by_plural = {role.plural or role.key: role for role in relationship.roles}

                for role_plural, members_with_role in roles_json.items():
                    role = role_by_plural[role_plural]

                    if role.max is not None and len(members_with_role) > role.max:
                        raise errors.SituationParsingError(
                            [entity.plural, instance_id, role_plural],
                            f"There can be at most {role.max} {role_plural} in a {entity.key}. {len(members_with_role)} were declared in '{instance_id}'.",
                        )

                    for index_within_role, member_id in enumerate(members_with_role):
                        member_index = members_ids.index(member_id)
                        membership_array[member_index] = entity_index
                        member_role = (
                            role.subroles[index_within_role] if role.subroles else role
                        )
                        roles[member_index] = member_role

            if members_to_allocate:
                entity_ids = entity_ids + list(members_to_allocate)
                for member_id in members_to_allocate:
                    member_index = members_ids.index(member_id)
                    membership_array[member_index] = entity_ids.index(
                        member_id,
                    )
                    roles[member_index] = entity.flattened_roles[0]
                # Adjust previously computed ids and counts
                self.entity_ids[entity.key] = entity_ids
                self.entity_counts[entity.key] = len(entity_ids)

            # Convert back to Python array

            self.memberships[relationship.name] = membership_array.tolist()
            self.roles[relationship.name] = roles.tolist()

    def save_memberships(self, simulation: Simulation) -> None:
        for (relationship_name, membership_array) in self.memberships.items():
            population = [p for n, p in simulation.populations.items() if relationship_name in [r.name for r in p.entity.relationships]].pop(0)
            membership = [m for m in population.memberships if m.relationship.name == relationship_name].pop(0)
            membership.members_entity_id = numpy.array(membership_array)
            membership.members_role = numpy.array(self.roles[relationship_name])


    def set_default_period(self, period_str) -> None:
        if period_str:
            self.default_period = str(periods.period(period_str))

    def get_input(self, variable: str, period_str: str) -> Array | None:
        if variable not in self.input_buffer:
            self.input_buffer[variable] = {}

        return self.input_buffer[variable].get(period_str)

    def check_members_to_allocate(
        self,
        members_plural,
        entity_plural,
        members_ids,
        member_id,
        entity_id,
        role_id,
        members_to_allocate,
        index,
    ) -> None:
        helpers.check_type(
            member_id,
            str,
            [entity_plural, entity_id, role_id, str(index)],
        )
        if member_id not in members_ids:
            raise errors.SituationParsingError(
                [entity_plural, entity_id, role_id],
                f"Unexpected value: {member_id}. {member_id} has been declared in {entity_id} {role_id}, but has not been declared in {members_plural}.",
            )
        if member_id not in members_to_allocate:
            raise errors.SituationParsingError(
                [entity_plural, entity_id, role_id],
                f"{member_id} has been declared more than once in {entity_plural}",
            )

    def init_variable_values(self, entity, instance_object, instance_id) -> None:
        for variable_name, variable_values in instance_object.items():
            path_in_json = [entity.plural, instance_id, variable_name]

            if variable_name in entity.roles:
                continue
            try:
                entity.check_variable_defined_for_entity(variable_name)
            except ValueError as e:  # The variable is defined for another entity
                raise errors.SituationParsingError(path_in_json, e.args[0])
            except errors.VariableNotFoundError as e:  # The variable doesn't exist
                raise errors.SituationParsingError(path_in_json, str(e), code=404)

            instance_index = self.get_ids(entity.key).index(instance_id)

            if not isinstance(variable_values, dict):
                if self.default_period is None:
                    raise errors.SituationParsingError(
                        path_in_json,
                        "Can't deal with type: expected object. Input variables should be set for specific periods. For instance: {'salary': {'2017-01': 2000, '2017-02': 2500}}, or {'birth_date': {'ETERNITY': '1980-01-01'}}.",
                    )
                variable_values = {self.default_period: variable_values}

            for period_str, value in variable_values.items():
                try:
                    periods.period(period_str)
                except ValueError as e:
                    raise errors.SituationParsingError(path_in_json, e.args[0])
                variable = entity.get_variable(variable_name)
                self.add_variable_value(
                    entity,
                    variable,
                    instance_index,
                    instance_id,
                    period_str,
                    value,
                )

    def add_variable_value(
        self,
        entity,
        variable,
        instance_index,
        instance_id,
        period_str,
        value,
    ) -> None:
        path_in_json = [entity.plural, instance_id, variable.name, period_str]

        if value is None:
            return

        array = self.get_input(variable.name, str(period_str))

        if array is None:
            array_size = self.get_count(entity.key)
            array = variable.default_array(array_size)

        try:
            value = variable.check_set_value(value)
        except ValueError as error:
            raise errors.SituationParsingError(path_in_json, *error.args)

        array[instance_index] = value

        self.input_buffer[variable.name][str(periods.period(period_str))] = array

    def finalize_variables_init(self, population) -> None:
        # Due to set_input mechanism, we must bufferize all inputs, then actually set them,
        # so that the months are set first and the years last.

        population.count = self.get_count(population.entity.key)
        population.ids = self.get_ids(population.entity.key)
        for variable_name in self.input_buffer:
            try:
                holder = population.get_holder(variable_name)
            except ValueError:  # Wrong entity, we can just ignore that
                continue
            buffer = self.input_buffer[variable_name]
            unsorted_periods = [
                periods.period(period_str)
                for period_str in self.input_buffer[variable_name]
            ]
            # We need to handle small periods first for set_input to work
            sorted_periods = sorted(unsorted_periods, key=periods.key_period_size)
            for period_value in sorted_periods:
                values = buffer[str(period_value)]
                # Hack to replicate the values in the persons entity
                # when we have an axis along a group entity but not persons
                array = numpy.tile(values, population.count // len(values))
                variable = holder.variable
                # TODO - this duplicates the check in Simulation.set_input, but
                # fixing that requires improving Simulation's handling of entities
                if (variable.end is None) or (period_value.start.date <= variable.end):
                    holder.set_input(period_value, array)

    def raise_period_mismatch(self, entity, json, e) -> NoReturn:
        # This error happens when we try to set a variable value for a period that doesn't match its definition period
        # It is only raised when we consume the buffer. We thus don't know which exact key caused the error.
        # We do a basic research to find the culprit path
        culprit_path = next(
            dpath.search(
                json,
                f"*/{e.variable_name}/{e.period!s}",
                yielded=True,
            ),
            None,
        )
        if culprit_path:
            path = [entity.plural, *culprit_path[0].split("/")]
        else:
            path = [
                entity.plural,
            ]  # Fallback: if we can't find the culprit, just set the error at the entities level

        raise errors.SituationParsingError(path, e.message)

    # Returns the total number of instances of this entity, including when there is replication along axes
    def get_count(self, entity_key: entities.Entity.key) -> int:
        return self.axes_entity_counts.get(entity_key, self.entity_counts[entity_key])

    # Returns the ids of instances of this entity, including when there is replication along axes
    def get_ids(self, entity_key: entities.Entity.key) -> list[str]:
        return self.axes_entity_ids.get(entity_key, self.entity_ids[entity_key])

    # Returns the memberships of individuals in this entity, including when there is replication along axes
    def get_memberships(self, relationship_name: entities.Relationship.name):
        # Return empty array for the "persons" entity
        return self.axes_memberships.get(
            relationship_name,
            self.memberships.get(relationship_name, []),
        )

    # Returns the roles of individuals in this entity, including when there is replication along axes
    def get_roles(self, relationship_name: entities.Relationship.name) -> Sequence[Role]:
        # Return empty array for the "persons" entity
        return self.axes_roles.get(relationship_name, self.roles.get(relationship_name, []))

    def add_parallel_axis(self, axis: Axis) -> None:
        # All parallel axes have the same count and entity.
        # Search for a compatible axis, if none exists, error out
        self.axes[0].append(axis)

    def add_perpendicular_axis(self, axis: Axis) -> None:
        # This adds an axis perpendicular to all previous dimensions
        self.axes.append([axis])

    def expand_axes(self) -> None:
        # This method should be idempotent & allow change in axes
        perpendicular_dimensions: list[list[Axis]] = self.axes
        cell_count: int = 1

        for parallel_axes in perpendicular_dimensions:
            first_axis: Axis = parallel_axes[0]
            axis_count: int = first_axis["count"]
            cell_count *= axis_count

        # Scale the "prototype" situation, repeating it cell_count times
        for entity_key in self.entity_ids:
            # Adjust counts
            self.axes_entity_counts[entity_key] = (
                self.get_count(entity_key) * cell_count
            )
            # Adjust ids
            original_ids: list[str] = self.get_ids(entity_key) * cell_count
            indices: Array[numpy.int16] = numpy.arange(
                0,
                cell_count * self.entity_counts[entity_key],
            )
            adjusted_ids: list[str] = [
                original_id + str(index)
                for original_id, index in zip(original_ids, indices)
            ]
            self.axes_entity_ids[entity_key] = adjusted_ids

            entity = self.axes_entity_map[entity_key]
            for relationship in entity.relationships:
                if relationship.a.key != entity.key:
                    continue
                # Adjust roles
                original_roles = self.get_roles(relationship.name)
                adjusted_roles = original_roles * cell_count
                self.axes_roles[relationship.name] = adjusted_roles

                # Adjust memberships, for group entities only
                original_memberships = self.get_memberships(relationship.name)
                repeated_memberships = original_memberships * cell_count
                indices = (
                    numpy.repeat(numpy.arange(0, cell_count), len(original_memberships))
                    * self.entity_counts[entity_key]
                )
                adjusted_memberships = (
                    numpy.array(repeated_memberships) + indices
                ).tolist()
                self.axes_memberships[relationship.name] = adjusted_memberships

        # Now generate input values along the specified axes
        # TODO - factor out the common logic here
        if len(self.axes) == 1 and len(self.axes[0]):
            parallel_axes = self.axes[0]
            first_axis = parallel_axes[0]
            axis_count: int = first_axis["count"]
            axis_entity = self.get_variable_entity(first_axis["name"])
            axis_entity_step_size = self.entity_counts[axis_entity.key]
            # Distribute values along axes
            for axis in parallel_axes:
                axis_index = axis.get("index", 0)
                axis_period = axis.get("period", self.default_period)
                axis_name = axis["name"]
                variable = axis_entity.get_variable(axis_name)
                array = self.get_input(axis_name, str(axis_period))
                if array is None:
                    array = variable.default_array(axis_count * axis_entity_step_size)
                elif array.size == axis_entity_step_size:
                    array = numpy.tile(array, axis_count)
                array[axis_index::axis_entity_step_size] = numpy.linspace(
                    axis["min"],
                    axis["max"],
                    num=axis_count,
                )
                # Set input
                self.input_buffer[axis_name][str(axis_period)] = array
        else:
            first_axes_count: list[int] = (
                parallel_axes[0]["count"] for parallel_axes in self.axes
            )
            axes_linspaces = [
                numpy.linspace(0, axis_count - 1, num=axis_count)
                for axis_count in first_axes_count
            ]
            axes_meshes = numpy.meshgrid(*axes_linspaces)
            for parallel_axes, mesh in zip(self.axes, axes_meshes):
                first_axis = parallel_axes[0]
                axis_count = first_axis["count"]
                axis_entity = self.get_variable_entity(first_axis["name"])
                axis_entity_step_size = self.entity_counts[axis_entity.key]
                # Distribute values along the grid
                for axis in parallel_axes:
                    axis_index = axis.get("index", 0)
                    axis_period = axis.get("period", self.default_period)
                    axis_name = axis["name"]
                    variable = axis_entity.get_variable(axis_name, check_existence=True)
                    array = self.get_input(axis_name, str(axis_period))
                    if array is None:
                        array = variable.default_array(
                            cell_count * axis_entity_step_size,
                        )
                    elif array.size == axis_entity_step_size:
                        array = numpy.tile(array, cell_count)
                    array[axis_index::axis_entity_step_size] = axis[
                        "min"
                    ] + mesh.reshape(cell_count) * (axis["max"] - axis["min"]) / (
                        axis_count - 1
                    )
                    self.input_buffer[axis_name][str(axis_period)] = array

    def get_variable_entity(self, variable_name: str) -> Entity:
        return self.variable_entities[variable_name]

    def register_variable(self, variable_name: str, entity: Entity) -> None:
        self.variable_entities[variable_name] = entity

    def register_variables(self, simulation: Simulation) -> None:
        tax_benefit_system: TaxBenefitSystem = simulation.tax_benefit_system
        variables: Iterable[str] = tax_benefit_system.variables.keys()

        for name in variables:
            population: Population = simulation.get_variable_population(name)
            entity: Entity = population.entity
            self.register_variable(name, entity)
