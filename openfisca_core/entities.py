# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
import traceback
import warnings
import textwrap
from os import linesep
from datetime import date

import numpy as np
import dpath

from openfisca_core.indexed_enums import Enum, EnumArray
from openfisca_core.scenarios import iter_over_entity_members
from openfisca_core.simulations import check_type, SituationParsingError
from openfisca_core.holders import Holder, PeriodMismatchError
from openfisca_core.periods import key_period_size, period as make_period
from openfisca_core.errors import VariableNotFound
from openfisca_core.commons import basestring_type

ADD = 'add'
DIVIDE = 'divide'


class Entity(object):
    """
        Represents an entity (e.g. a person, a household, etc.) on which calculations can be run.
    """
    key = None
    plural = None
    label = None
    doc = ""
    is_person = False

    def __init__(self, simulation, entities_json = None):
        self.simulation = simulation
        self._holders = {}
        if entities_json is not None:
            self.init_from_json(entities_json)
        else:
            self.entities_json = None
            self.count = 0
            self.ids = []
            self.step_size = 0

    def init_from_json(self, entities_json):
        """
            Initilalises entities from a JSON dictionnary.

            This method, still under experimentation, aims at replacing the initialisation from `scenario.make_json_or_python_to_attributes`
        """
        check_type(entities_json, dict, [self.plural])
        self.entities_json = entities_json
        self.count = len(entities_json)
        self.step_size = self.count  # Related to axes.
        self.ids = sorted(entities_json.keys())
        for entity_id, entity_object in entities_json.items():
            check_type(entity_object, dict, [self.plural, entity_id])
            if not self.is_person:
                roles_json, variables_json = self.split_variables_and_roles_json(entity_object)
                self.init_members(roles_json, entity_id)
            else:
                variables_json = entity_object
            self.init_variable_values(variables_json, entity_id)

        # Due to set_input mechanism, we must bufferize all inputs, then actually set them, so that the months are set first and the years last.
        self.finalize_variables_init()

    def init_variable_values(self, entity_object, entity_id):
        entity_index = self.ids.index(entity_id)
        for variable_name, variable_values in entity_object.items():
            path_in_json = [self.plural, entity_id, variable_name]
            try:
                self.check_variable_defined_for_entity(variable_name)
            except ValueError as e:  # The variable is defined for another entity
                raise SituationParsingError(path_in_json, e.args[0])
            except VariableNotFound as e:  # The variable doesn't exist
                raise SituationParsingError(path_in_json, e.message, code = 404)

            if not isinstance(variable_values, dict):
                raise SituationParsingError(path_in_json,
                    "Invalid type: must be of type object. Input variables must be set for specific periods. For instance: {'salary': {'2017-01': 2000, '2017-02': 2500}}, or {'birth_date': {'ETERNITY': '1980-01-01'}}.")

            holder = self.get_holder(variable_name)
            for period_str, value in variable_values.items():
                path_in_json.append(period_str)
                try:
                    period = make_period(period_str)
                except ValueError as e:
                    raise SituationParsingError(path_in_json, e.args[0])
                if value is not None:
                    array = holder.buffer.get(period)
                    if array is None:
                        array = holder.default_array()
                    if holder.variable.value_type == Enum and isinstance(value, basestring_type):
                        try:
                            value = holder.variable.possible_values[value].index
                        except KeyError:
                            possible_values = [item.name for item in holder.variable.possible_values]
                            raise SituationParsingError(path_in_json,
                                "'{}' is not a valid value for '{}'. Possible values are ['{}'].".format(
                                    value, variable_name, "', '".join(possible_values))
                                )
                    try:
                        array[entity_index] = value
                    except (ValueError, TypeError):
                        if holder.variable.value_type == date:
                            error_message = "Invalid date: '{}'.".format(value)
                        else:
                            error_message = "Invalid value: must be of type {}, received '{}'.".format(holder.variable.json_type, value)
                        raise SituationParsingError(path_in_json, error_message)

                    holder.buffer[period] = array

    def finalize_variables_init(self):
        for variable_name, holder in self._holders.items():
            periods = holder.buffer.keys()
            # We need to handle small periods first for set_input to work
            sorted_periods = sorted(periods, key=key_period_size)
            for period in sorted_periods:
                array = holder.buffer[period]
                try:
                    holder.set_input(period, array)
                except PeriodMismatchError as e:
                    # This errors happens when we try to set a variable value for a period that doesn't match its definition period
                    # It is only raised when we consume the buffer. We thus don't know which exact key caused the error.
                    # We do a basic research to find the culprit path
                    culprit_path = next(
                        dpath.search(self.entities_json, "*/{}/{}".format(e.variable_name, str(e.period)), yielded = True),
                        None)
                    if culprit_path:
                        path = [self.plural] + culprit_path[0].split('/')
                    else:
                        path = [self.plural]  # Fallback: if we can't find the culprit, just set the error at the entities level

                    raise SituationParsingError(path, e.message)

    def clone(self, new_simulation):
        """
            Returns an entity instance with the same structure, but no variable value set.
        """
        new = self.__class__(new_simulation)
        new_dict = new.__dict__

        for key, value in self.__dict__.items():
            if key == '_holders':
                new_dict[key] = {
                    name: holder.clone(new)
                    for name, holder in self._holders.items()
                    }
            elif key != 'simulation':
                new_dict[key] = value

        return new

    def __getattr__(self, attribute):
        projector = get_projector_from_shortcut(self, attribute)
        if not projector:
            raise AttributeError("Entity {} has no attribute {}".format(self.key, attribute))
        return projector

    @classmethod
    def to_json(cls):
        return {
            'isPersonsEntity': cls.is_person,
            'key': cls.key,
            'label': cls.label,
            'plural': cls.plural,
            'doc': cls.doc,
            'roles': cls.roles_description,
            }

    # Calculations

    def check_variable_defined_for_entity(self, variable_name):
        variable_entity = self.simulation.tax_benefit_system.get_variable(variable_name, check_existence = True).entity
        if not isinstance(self, variable_entity):
            message = linesep.join([
                "You tried to compute the variable '{0}' for the entity '{1}';".format(variable_name, self.plural),
                "however the variable '{0}' is defined for '{1}'.".format(variable_name, variable_entity.plural),
                "Learn more about entities in our documentation:",
                "<http://openfisca.org/doc/coding-the-legislation/50_entities.html>."])
            raise ValueError(message)

    def check_array_compatible_with_entity(self, array):
        if not self.count == array.size:
            raise ValueError("Input {} is not a valid value for the entity {}".format(array, self.key))

    def check_role_validity(self, role):
        if role is not None and not type(role) == Role:
            raise ValueError("{} is not a valid role".format(role))

    def check_period_validity(self, variable_name, period):
        if period is None:
            stack = traceback.extract_stack()
            filename, line_number, function_name, line_of_code = stack[-3]
            raise ValueError('''
You requested computation of variable "{}", but you did not specify on which period in "{}:{}":
    {}
When you request the computation of a variable within a formula, you must always specify the period as the second parameter. The convention is to call this parameter "period". For example:
    computed_salary = person('salary', period).
See more information at <http://openfisca.org/doc/coding-the-legislation/35_periods.html#periods-for-variable>.
'''.format(variable_name, filename, line_number, line_of_code).encode('utf-8'))

    def __call__(self, variable_name, period = None, options = [], **parameters):
        """
            Calculate the variable ``variable_name`` for the entity and the period ``period``, using the variable formula if it exists.

            Example:

            >>> person('salary', '2017-04')
            >>> array([300.])

            :returns: A numpy array containing the result of the calculation
        """
        self.check_variable_defined_for_entity(variable_name)

        self.check_period_validity(variable_name, period)

        if ADD in options and DIVIDE in options:
            raise ValueError('Options ADD and DIVIDE are incompatible (trying to compute variable {})'.format(variable_name).encode('utf-8'))
        elif ADD in options:
            return self.simulation.calculate_add(variable_name, period, **parameters)
        elif DIVIDE in options:
            return self.simulation.calculate_divide(variable_name, period, **parameters)
        else:
            return self.simulation.calculate(variable_name, period, **parameters)

    # Helpers

    def empty_array(self):
        return np.zeros(self.count)

    def filled_array(self, value, dtype = None):
        with warnings.catch_warnings():  # Avoid a non-relevant warning
            warnings.simplefilter("ignore")
            return np.full(self.count, value, dtype)

    def get_holder(self, variable_name):
        self.check_variable_defined_for_entity(variable_name)
        holder = self._holders.get(variable_name)
        if holder:
            return holder
        variable = self.simulation.tax_benefit_system.get_variable(variable_name)
        self._holders[variable_name] = holder = Holder(
            entity = self,
            variable = variable,
            )
        return holder

    def get_memory_usage(self, variables = None):
        holders_memory_usage = {
            variable_name: holder.get_memory_usage()
            for variable_name, holder in self._holders.items()
            if variables is None or variable_name in variables
            }

        total_memory_usage = sum(
            holder_memory_usage['total_nb_bytes'] for holder_memory_usage in holders_memory_usage.values()
            )

        return dict(
            total_nb_bytes = total_memory_usage,
            by_variable = holders_memory_usage
            )


def projectable(function):
    """
    Decorator to indicate that when called on a projector, the outcome of the function must be projected.
    For instance person.household.sum(...) must be projected on person, while it would not make sense for person.household.get_holder.
    """
    function.projectable = True
    return function


class PersonEntity(Entity):
    """
        Represents a person on which calculations are run.
    """
    is_person = True

    # Projection person -> person

    @projectable
    def has_role(self, role):
        """
            Check if a person has a given role within its :any:`GroupEntity`

            Exemple:

            >>> person.has_role(Household.CHILD)
            >>> array([False])
        """
        self.check_role_validity(role)
        entity = self.simulation.get_entity(role.entity_class)
        if role.subroles:
            return np.logical_or.reduce([entity.members_role == subrole for subrole in role.subroles])
        else:
            return entity.members_role == role

    @projectable
    def value_from_partner(self, array, entity, role):
        self.check_array_compatible_with_entity(array)
        self.check_role_validity(role)

        if not role.subroles or not len(role.subroles) == 2:
            raise Exception('Projection to partner is only implemented for roles having exactly two subroles.')

        [subrole_1, subrole_2] = role.subroles
        value_subrole_1 = entity.value_from_person(array, subrole_1)
        value_subrole_2 = entity.value_from_person(array, subrole_2)

        return np.select(
            [self.has_role(subrole_1), self.has_role(subrole_2)],
            [value_subrole_2, value_subrole_1],
            )

    @projectable
    def get_rank(self, entity, criteria, condition = True):
        """
        Get the rank of a person within an entity according to a criteria.
        The person with rank 0 has the minimum value of criteria.
        If condition is specified, then the persons who don't respect it are not taken into account and their rank is -1.

        Exemple:

        >>> age = person('age', period)  # e.g [32, 34, 2, 8, 1]
        >>> person.get_rank(household, age)
        >>> [3, 4, 0, 2, 1]

        >>> is_child = person.has_role(Household.CHILD)  # [False, False, True, True, True]
        >>> person.get_rank(household, - age, condition = is_child)  # Sort in reverse order so that the eldest child gets the rank 0.
        >>> [-1, -1, 1, 0, 2]
        """

        # If entity is for instance 'person.household', we get the reference entity 'household' behind the projector
        entity = entity if not isinstance(entity, Projector) else entity.reference_entity

        positions = entity.members_position
        biggest_entity_size = np.max(positions) + 1
        filtered_criteria = np.where(condition, criteria, np.inf)
        ids = entity.members_entity_id

        # Matrix: the value in line i and column j is the value of criteria for the jth person of the ith entity
        matrix = np.asarray([
            entity.value_nth_person(k, filtered_criteria, default = np.inf)
            for k in range(biggest_entity_size)
            ]).transpose()

        # We double-argsort all lines of the matrix.
        # Double-argsorting gets the rank of each value once sorted
        # For instance, if x = [3,1,6,4,0], y = np.argsort(x) is [4, 1, 0, 3, 2] (because the value with index 4 is the smallest one, the value with index 1 the second smallest, etc.) and z = np.argsort(y) is [2, 1, 4, 3, 0], the rank of each value.
        sorted_matrix = np.argsort(np.argsort(matrix))

        # Build the result vector by taking for each person the value in the right line (corresponding to its household id) and the right column (corresponding to its position)
        result = sorted_matrix[ids, positions]

        # Return -1 for the persons who don't respect the condition
        return np.where(condition, result, -1)


class GroupEntity(Entity):
    """
        Represents an entity composed of several persons with different roles, on which calculations are run.
    """

    roles = None
    flattened_roles = None
    roles_description = None

    def __init__(self, simulation, entities_json = None):
        Entity.__init__(self, simulation, entities_json)
        if entities_json is None:
            self.members_entity_id = None
            self._members_role = None
            self._members_position = None
            self.members_legacy_role = None
        self.members = self.simulation.persons
        self._roles_count = None
        self._ordered_members_map = None

    def split_variables_and_roles_json(self, entity_object):
        entity_object = entity_object.copy()  # Don't mutate function input

        roles_definition = {
            role.plural or role.key: entity_object.pop(role.plural or role.key, [])
            for role in self.roles
            }
        return roles_definition, entity_object

    def init_from_json(self, entities_json):
        self.members_entity_id = np.empty(
            self.simulation.persons.count,
            dtype = np.int32
            )
        self.members_role = np.empty(
            self.simulation.persons.count,
            dtype = object
            )
        self.members_legacy_role = np.empty(
            self.simulation.persons.count,
            dtype = np.int32
            )
        self._members_position = None

        self.persons_to_allocate = set(self.simulation.persons.ids)

        Entity.init_from_json(self, entities_json)

        if self.persons_to_allocate:
            unallocated_person = self.persons_to_allocate.pop()
            raise SituationParsingError([self.plural],
                '{0} has been declared in {1}, but is not a member of any {2}. All {1} must be allocated to a {2}.'.format(
                    unallocated_person, self.simulation.persons.plural, self.key)
                )

    def init_members(self, roles_json, entity_id):
        for role_id, role_definition in roles_json.items():
            check_type(role_definition, list, [self.plural, entity_id, role_id])
            for index, person_id in enumerate(role_definition):
                check_type(person_id, basestring_type, [self.plural, entity_id, role_id, str(index)])
                if person_id not in self.simulation.persons.ids:
                    raise SituationParsingError([self.plural, entity_id, role_id],
                        "Unexpected value: {0}. {0} has been declared in {1} {2}, but has not been declared in {3}.".format(
                            person_id, entity_id, role_id, self.simulation.persons.plural)
                        )
                if person_id not in self.persons_to_allocate:
                    raise SituationParsingError([self.plural, entity_id, role_id],
                        "{} has been declared more than once in {}".format(
                            person_id, self.plural)
                        )
                self.persons_to_allocate.discard(person_id)

        entity_index = self.ids.index(entity_id)
        for person_role, person_legacy_role, person_id in iter_over_entity_members(self, roles_json):
            person_index = self.simulation.persons.ids.index(person_id)
            self.members_entity_id[person_index] = entity_index
            self.members_role[person_index] = person_role
            self.members_legacy_role[person_index] = person_legacy_role

    @property
    def members_role(self):
        if self._members_role is None and self.members_legacy_role is not None:
            self._members_role = np.asarray([
                self.flattened_roles[legacy_role] if legacy_role < len(self.flattened_roles) else self.flattened_roles[-1]
                for legacy_role in self.members_legacy_role
                ])
        return self._members_role

    @property
    def members_position(self):
        if self._members_position is None and self.members_entity_id is not None:
            # We could use self.count and self.members.count , but with the current initilization, we are not sure count will be set before members_position is called
            nb_entities = np.max(self.members_entity_id) + 1
            nb_persons = len(self.members_entity_id)
            self._members_position = np.empty_like(self.members_entity_id)
            counter_by_entity = np.zeros(nb_entities)
            for k in range(nb_persons):
                entity_index = self.members_entity_id[k]
                self._members_position[k] = counter_by_entity[entity_index]
                counter_by_entity[entity_index] += 1

        return self._members_position

    @members_role.setter
    def members_role(self, members_role):
        self._members_role = members_role

    @members_position.setter
    def members_position(self, members_position):
        self._members_position = members_position

    @property
    def roles_count(self):
        warnings.warn(' '.join([
            "entity.roles_count is deprecated.",
            "Since OpenFisca Core 23.0, this attribute has strictly no effect, and it is not necessary to set it."
            ]),
            Warning
            )
        if self._roles_count is None:
            self._roles_count = self.members_legacy_role.max() + 1
        return self._roles_count

    @roles_count.setter
    def roles_count(self, value):
        warnings.warn(' '.join([
            "entity.roles_count is deprecated.",
            "Since OpenFisca Core 23.0, this attribute has strictly no effect, and it is not necessary to set it."
            ]),
            Warning
            )
        self._roles_count = value

    @property
    def ordered_members_map(self):
        """
        Mask to group the persons by entity
        This function only caches the map value, to see what the map is used for, see value_nth_person method.
        """
        if self._ordered_members_map is None:
            return np.argsort(self.members_entity_id)
        return self._ordered_members_map

    #  Aggregation persons -> entity

    @projectable
    def sum(self, array, role = None):
        """
            Return the sum of ``array`` for the members of the entity.

            ``array`` must have the dimension of the number of persons in the simulation

            If ``role`` is provided, only the entity member with the given role are taken into account.

            Example:

            >>> salaries = household.members('salary', '2018-01')  # e.g. [2000, 1500, 0, 0, 0]
            >>> household.sum(salaries)
            >>> array([3500])
        """
        self.check_role_validity(role)
        self.simulation.persons.check_array_compatible_with_entity(array)
        if role is not None:
            role_filter = self.members.has_role(role)
            return np.bincount(
                self.members_entity_id[role_filter],
                weights = array[role_filter],
                minlength = self.count)
        else:
            return np.bincount(self.members_entity_id, weights = array)

    @projectable
    def any(self, array, role = None):
        """
            Return ``True`` if ``array`` is ``True`` for any members of the entity.

            ``array`` must have the dimension of the number of persons in the simulation

            If ``role`` is provided, only the entity member with the given role are taken into account.

            Example:

            >>> salaries = household.members('salary', '2018-01')  # e.g. [2000, 1500, 0, 0, 0]
            >>> household.any(salaries >= 1800)
            >>> array([True])
        """
        sum_in_entity = self.sum(array, role = role)
        return (sum_in_entity > 0)

    @projectable
    def reduce(self, array, reducer, neutral_element, role = None):
        self.simulation.persons.check_array_compatible_with_entity(array)
        self.check_role_validity(role)
        position_in_entity = self.members_position
        role_filter = self.members.has_role(role) if role is not None else True
        filtered_array = np.where(role_filter, array, neutral_element)

        result = self.filled_array(neutral_element)  # Neutral value that will be returned if no one with the given role exists.

        # We loop over the positions in the entity
        # Looping over the entities is tempting, but potentielly slow if there are a lot of entities
        biggest_entity_size = np.max(position_in_entity) + 1

        for p in range(biggest_entity_size):
            result = reducer(result, self.value_nth_person(p, filtered_array, default = neutral_element))

        return result

    @projectable
    def all(self, array, role = None):
        """
            Return ``True`` if ``array`` is ``True`` for all members of the entity.

            ``array`` must have the dimension of the number of persons in the simulation

            If ``role`` is provided, only the entity member with the given role are taken into account.

            Example:

            >>> salaries = household.members('salary', '2018-01')  # e.g. [2000, 1500, 0, 0, 0]
            >>> household.all(salaries >= 1800)
            >>> array([False])
        """
        return self.reduce(array, reducer = np.logical_and, neutral_element = True, role = role)

    @projectable
    def max(self, array, role = None):
        """
            Return the maximum value of ``array`` for the entity members.

            ``array`` must have the dimension of the number of persons in the simulation

            If ``role`` is provided, only the entity member with the given role are taken into account.

            Example:

            >>> salaries = household.members('salary', '2018-01')  # e.g. [2000, 1500, 0, 0, 0]
            >>> household.max(salaries)
            >>> array([2000])
        """
        return self.reduce(array, reducer = np.maximum, neutral_element = - np.infty, role = role)

    @projectable
    def min(self, array, role = None):
        """
            Return the minimum value of ``array`` for the entity members.

            ``array`` must have the dimension of the number of persons in the simulation

            If ``role`` is provided, only the entity member with the given role are taken into account.

            Example:

            >>> salaries = household.members('salary', '2018-01')  # e.g. [2000, 1500, 0, 0, 0]
            >>> household.min(salaries)
            >>> array([0])
            >>> household.min(salaries, role = Household.PARENT)  # Assuming the 1st two persons are parents
            >>> array([1500])
        """
        return self.reduce(array, reducer = np.minimum, neutral_element = np.infty, role = role)

    @projectable
    def nb_persons(self, role = None):
        """
            Returns the number of persons contained in the entity.

            If ``role`` is provided, only the entity member with the given role are taken into account.
        """
        if role:
            role_condition = self.members.has_role(role)
            return self.sum(role_condition)
        else:
            return np.bincount(self.members_entity_id)

    # Projection person -> entity

    @projectable
    def value_from_person(self, array, role, default = 0):
        """
            Get the value of ``array`` for the person with the unique role ``role``.

            ``array`` must have the dimension of the number of persons in the simulation

            If such a person does not exist, return ``default`` instead

            The result is a vector which dimension is the number of entities
        """
        self.check_role_validity(role)
        if role.max != 1:
            raise Exception(
                'You can only use value_from_person with a role that is unique in {}. Role {} is not unique.'
                .format(self.key, role.key)
                )
        self.simulation.persons.check_array_compatible_with_entity(array)
        members_map = self.ordered_members_map
        result = self.filled_array(default, dtype = array.dtype)
        if isinstance(array, EnumArray):
            result = EnumArray(result, array.possible_values)
        role_filter = self.members.has_role(role)
        entity_filter = self.any(role_filter)

        result[entity_filter] = array[members_map][role_filter[members_map]]

        return result

    @projectable
    def value_nth_person(self, n, array, default = 0):
        """
            Get the value of array for the person whose position in the entity is n.

            Note that this position is arbitrary, and that members are not sorted.

            If the nth person does not exist, return  ``default`` instead.

            The result is a vector which dimension is the number of entities.
        """
        self.simulation.persons.check_array_compatible_with_entity(array)
        positions = self.members_position
        nb_persons_per_entity = self.nb_persons()
        members_map = self.ordered_members_map
        result = self.filled_array(default, dtype = array.dtype)
        # For households that have at least n persons, set the result as the value of criteria for the person for which the position is n.
        # The map is needed b/c the order of the nth persons of each household in the persons vector is not necessarily the same than the household order.
        result[nb_persons_per_entity > n] = array[members_map][positions[members_map] == n]

        return result

    @projectable
    def value_from_first_person(self, array):
        return self.value_nth_person(0, array)

    # Projection entity -> person(s)

    def project(self, array, role = None):
        self.check_array_compatible_with_entity(array)
        self.check_role_validity(role)
        if role is None:
            return array[self.members_entity_id]
        else:
            role_condition = self.members.has_role(role)
            return np.where(role_condition, array[self.members_entity_id], 0)

    # Does it really make sense ? Should not we use roles instead of position when projecting on someone in particular ?
    # Doesn't seem to be used, maybe should just not introduce
    def project_on_first_person(self, array):
        self.check_array_compatible_with_entity(array)
        entity_position_array = self.members_position
        entity_index_array = self.members_entity_id
        position_filter = (entity_position_array == 0)
        return np.where(position_filter, array[entity_index_array], 0)

    @projectable
    def share_between_members(self, array, role = None):
        self.check_array_compatible_with_entity(array)
        self.check_role_validity(role)
        nb_persons_per_entity = self.nb_persons(role)
        return self.project(array / nb_persons_per_entity, role = role)

    # Projection entity -> entity

    # Doesn't seem to be used either, as we can do entity1.first_person.entity2
    # Maybe should not introduce
    @projectable
    def transpose(self, array, origin_entity):
        origin_entity = self.simulation.get_entity(origin_entity)
        origin_entity.check_array_compatible_with_entity(array)
        input_projected = origin_entity.project(array)
        return self.value_from_first_person(input_projected)


class Role(object):

    def __init__(self, description, entity):
        self.entity_class = entity
        self.key = description['key']
        self.label = description.get('label')
        self.plural = description.get('plural')
        self.doc = textwrap.dedent(description.get('doc', ""))
        self.max = description.get('max')
        self.subroles = None

    def __repr__(self):
        return "Role({})".format(self.key)


class Projector(object):
    reference_entity = None
    parent = None

    def __getattr__(self, attribute):
        projector = get_projector_from_shortcut(self.reference_entity, attribute, parent = self)
        if projector:
            return projector

        reference_attr = getattr(self.reference_entity, attribute)
        if not hasattr(reference_attr, 'projectable'):
            return reference_attr

        def projector_function(*args, **kwargs):
            result = reference_attr(*args, **kwargs)
            return self.transform_and_bubble_up(result)

        return projector_function

    def __call__(self, *args, **kwargs):
        result = self.reference_entity(*args, **kwargs)
        return self.transform_and_bubble_up(result)

    def transform_and_bubble_up(self, result):
        transformed_result = self.transform(result)
        if self.parent is None:
            return transformed_result
        else:
            return self.parent.transform_and_bubble_up(transformed_result)

    def transform(self, result):
        return NotImplementedError()


# For instance person.family
class EntityToPersonProjector(Projector):

    def __init__(self, entity, parent = None):
        self.reference_entity = entity
        self.parent = parent

    def transform(self, result):
        return self.reference_entity.project(result)


# For instance famille.first_person
class FirstPersonToEntityProjector(Projector):

    def __init__(self, entity, parent = None):
        self.target_entity = entity
        self.reference_entity = entity.members
        self.parent = parent

    def transform(self, result):
        return self.target_entity.value_from_first_person(result)


# For instance famille.declarant_principal
class UniqueRoleToEntityProjector(Projector):

    def __init__(self, entity, role, parent = None):
        self.target_entity = entity
        self.reference_entity = entity.members
        self.parent = parent
        self.role = role

    def transform(self, result):
        return self.target_entity.value_from_person(result, self.role)


def build_entity(key, plural, label, doc = "", roles = None, is_person = False):
    entity_class_name = key.title()
    attributes = {'key': key, 'plural': plural, 'label': label, 'doc': textwrap.dedent(doc), 'roles_description': roles}
    if is_person:
        entity_class = type(entity_class_name, (PersonEntity,), attributes)
    elif roles:
        entity_class = type(entity_class_name, (GroupEntity,), attributes)
        entity_class.roles = []
        for role_description in roles:
            role = Role(role_description, entity_class)
            entity_class.roles.append(role)
            setattr(entity_class, role.key.upper(), role)
            if role_description.get('subroles'):
                role.subroles = []
                for subrole_key in role_description['subroles']:
                    subrole = Role({'key': subrole_key, 'max': 1}, entity_class)
                    setattr(entity_class, subrole.key.upper(), subrole)
                    role.subroles.append(subrole)
                role.max = len(role.subroles)
        entity_class.flattened_roles = sum([role2.subroles or [role2] for role2 in entity_class.roles], [])

    return entity_class


def get_projector_from_shortcut(entity, shortcut, parent = None):
    if entity.is_person:
        if shortcut in entity.simulation.entities:
            entity_2 = entity.simulation.entities[shortcut]
            return EntityToPersonProjector(entity_2, parent)
    else:
        if shortcut == 'first_person':
            return FirstPersonToEntityProjector(entity, parent)
        role = next((role for role in entity.flattened_roles if (role.max == 1) and (role.key == shortcut)), None)
        if role:
            return UniqueRoleToEntityProjector(entity, role, parent)
