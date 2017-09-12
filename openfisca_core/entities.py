# -*- coding: utf-8 -*-

import traceback
import warnings
import textwrap
from os import linesep

import numpy as np
import dpath

from formulas import ADD, DIVIDE
from scenarios import iter_over_entity_members
from simulations import check_type, SituationParsingError
from holders import Holder, PeriodMismatchError
from periods import compare_period_size, period as make_period
from taxbenefitsystems import VariableNotFound
from columns import EnumCol


class Entity(object):
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
        for entity_id, entity_object in entities_json.iteritems():
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
        for variable_name, variable_values in entity_object.iteritems():
            path_in_json = [self.plural, entity_id, variable_name]
            try:
                self.check_variable_defined_for_entity(variable_name)
            except ValueError as e:  # The variable is defined for another entity
                raise SituationParsingError(path_in_json, e.message)
            except VariableNotFound as e:  # The variable doesn't exist
                raise SituationParsingError(path_in_json, e.message, code = 404)

            if not isinstance(variable_values, dict):
                raise SituationParsingError(path_in_json,
                    'Invalid type: must be of type object. Input variables must be set for specific periods. For instance: {"salary": {"2017-01": 2000, "2017-02": 2500}}')

            holder = self.get_holder(variable_name)
            for date, value in variable_values.iteritems():
                path_in_json.append(date)
                try:
                    period = make_period(date)
                except ValueError as e:
                    raise SituationParsingError(path_in_json, e.message)
                if value is not None:
                    array = holder.buffer.get(period)
                    if array is None:
                        array = holder.default_array()
                    if isinstance(holder.column, EnumCol) and isinstance(value, basestring):
                        try:
                            value = holder.column.enum[value]
                        except KeyError:
                            raise SituationParsingError(path_in_json,
                                "'{}' is not a valid value for '{}'. Possible values are ['{}'].".format(
                                    value, variable_name, "', '".join(holder.column.enum.list)
                                    ).encode('utf-8')
                                )
                    try:
                        array[entity_index] = value
                    except (ValueError, TypeError) as e:
                        raise SituationParsingError(path_in_json,
                    'Invalid type: must be of type {}.'.format(holder.column.json_type))

                    holder.buffer[period] = array

    def finalize_variables_init(self):
        for variable_name, holder in self._holders.iteritems():
            periods = holder.buffer.keys()
            # We need to handle small periods first for set_input to work
            sorted_periods = sorted(periods, cmp = compare_period_size)
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

        for key, value in self.__dict__.iteritems():
            if key == '_holders':
                new_dict[key] = {
                    name: holder.clone(new)
                    for name, holder in self._holders.iteritems()
                    }
            elif key != 'simulation':
                new_dict[key] = value

        return new

    def __getattr__(self, attribute):
        projector = get_projector_from_shortcut(self, attribute)
        if not projector:
            raise Exception("Entity {} has no attribute {}".format(self.key, attribute))
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
        variable_entity = self.simulation.tax_benefit_system.get_column(variable_name, check_existence = True).entity
        if not isinstance(self, variable_entity):
            message = linesep.join([
                u"You tried to compute the variable '{0}' for the entity '{1}';".format(variable_name, self.plural),
                u"however the variable '{0}' is defined for '{1}'.".format(variable_name, variable_entity.plural),
                u"Learn more about entities in our documentation:",
                u"<http://openfisca.org/doc/coding-the-legislation/50_entities.html>."])
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
            raise ValueError(u'''
You requested computation of variable "{}", but you did not specify on which period in "{}:{}":
    {}
When you request the computation of a variable within a formula, you must always specify the period as the second parameter. The convention is to call this parameter "period". For example:
    computed_salary = person('salary', period).
See more information at <http://openfisca.org/doc/coding-the-legislation/35_periods.html#periods-for-variable>.
'''.format(variable_name, filename, line_number, line_of_code).encode('utf-8'))

    def __call__(self, variable_name, period = None, options = [], **parameters):
        self.check_variable_defined_for_entity(variable_name)

        self.check_period_validity(variable_name, period)

        if ADD in options and DIVIDE in options:
            raise ValueError(u'Options ADD and DIVIDE are incompatible (trying to compute variable {})'.format(variable_name).encode('utf-8'))
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
        column = self.simulation.tax_benefit_system.get_column(variable_name)
        self._holders[variable_name] = holder = Holder(
            entity = self,
            column = column,
            )
        if column.formula_class is not None:
            holder.formula = column.formula_class(holder = holder)  # Instanciates a Formula
        return holder


class PersonEntity(Entity):
    is_person = True

    # Projection person -> person

    def has_role(self, role):
        self.check_role_validity(role)
        entity = self.simulation.get_entity(role.entity_class)
        if role.subroles:
            return np.logical_or.reduce([entity.members_role == subrole for subrole in role.subroles])
        else:
            return entity.members_role == role

    def value_from_partner(self, array, entity, role):
        self.check_array_compatible_with_entity(array)
        self.check_role_validity(role)

        if not role.subroles or not len(role.subroles) == 2:
            raise Exception('Projection to partner is only implemented for roles having exactly two subroles.')

        [subrole_1, subrole_2] = role.subroles
        value_subrole_1 = entity.project(entity.value_from_person(array, subrole_1))
        value_subrole_2 = entity.project(entity.value_from_person(array, subrole_2))

        return np.select(
            [self.has_role(subrole_1), self.has_role(subrole_2)],
            [value_subrole_2, value_subrole_1],
            )


class GroupEntity(Entity):
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

        #  Deprecated attribute used by deprecated projection opertors, such as sum_by_entity
        self.roles_count = self.members_legacy_role.max() + 1

    def init_members(self, roles_json, entity_id):
        for role_id, role_definition in roles_json.iteritems():
            check_type(role_definition, list, [self.plural, entity_id, role_id])
            for index, person_id in enumerate(role_definition):
                check_type(person_id, basestring, [self.plural, entity_id, role_id, str(index)])
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

    #  Aggregation persons -> entity

    def sum(self, array, role = None):
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

    def any(self, array, role = None):
        sum_in_entity = self.sum(array, role = role)
        return (sum_in_entity > 0)

    def reduce(self, array, reducer, neutral_element, role = None):
        self.simulation.persons.check_array_compatible_with_entity(array)
        self.check_role_validity(role)
        position_in_entity = self.members_position
        role_filter = self.members.has_role(role) if role is not None else True

        result = self.filled_array(neutral_element)  # Neutral value that will be returned if no one with the given role exists.

        # We loop over the positions in the entity
        # Looping over the entities is tempting, but potentielly slow if there are a lot of entities
        nb_positions = np.max(position_in_entity) + 1
        for p in range(nb_positions):
            filter = (position_in_entity == p) * role_filter
            entity_filter = self.any(filter)
            result[entity_filter] = reducer(result[entity_filter], array[filter])

        return result

    def all(self, array, role = None):
        return self.reduce(array, reducer = np.logical_and, neutral_element = True, role = role)

    def max(self, array, role = None):
        return self.reduce(array, reducer = np.maximum, neutral_element = - np.infty, role = role)

    def min(self, array, role = None):
        return self.reduce(array, reducer = np.minimum, neutral_element = np.infty, role = role)

    def nb_persons(self, role = None):
        if role:
            role_condition = self.members.has_role(role)
            return self.sum(role_condition)
        else:
            return np.bincount(self.members_entity_id)

    # Projection person -> entity

    def value_from_person(self, array, role, default = 0):
        self.check_role_validity(role)
        if role.max != 1:
            raise Exception(
                'You can only use value_from_person with a role that is unique in {}. Role {} is not unique.'
                .format(self.key, role.key)
                )
        self.simulation.persons.check_array_compatible_with_entity(array)
        result = self.filled_array(default, dtype = array.dtype)
        role_filter = self.members.has_role(role)
        entity_filter = self.any(role_filter)

        result[entity_filter] = array[role_filter]

        return result

    def value_from_first_person(self, array):
        self.simulation.persons.check_array_compatible_with_entity(array)
        position_filter = (self.members_position == 0)

        return array[position_filter]

    # Projection entity -> person(s)

    def project(self, array, role = None):
        self.check_array_compatible_with_entity(array)
        self.check_role_validity(role)
        role_condition = self.members.has_role(role) if role is not None else True
        return np.where(role_condition, array[self.members_entity_id], 0)

    # Does it really make sense ? Should not we use roles instead of position when projecting on someone in particular ?
    # Doesn't seem to be used, maybe should just not introduce
    def project_on_first_person(self, array):
        self.check_array_compatible_with_entity(array)
        entity_position_array = self.members_position
        entity_index_array = self.members_entity_id
        position_filter = (entity_position_array == 0)
        return np.where(position_filter, array[entity_index_array], 0)

    def share_between_members(self, array, role = None):
        self.check_array_compatible_with_entity(array)
        self.check_role_validity(role)
        nb_persons_per_entity = self.nb_persons(role)
        return self.project(array / nb_persons_per_entity, role = role)

    # Projection entity -> entity

    # Doesn't seem to be used either, as we can do entity1.first_person.entity2
    # Maybe should not introduce
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
        return (get_projector_from_shortcut(self.reference_entity, attribute, parent = self) or getattr(self.reference_entity, attribute))

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
