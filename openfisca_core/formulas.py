# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
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


import collections
import datetime
import inspect
import itertools
import logging
import textwrap

import numpy as np

from . import columns, holders, periods
from .tools import empty_clone, stringify_array


log = logging.getLogger(__name__)


# Exceptions


class NaNCreationError(Exception):
    pass


# Formulas


class AbstractFormula(object):
    holder = None

    def __init__(self, holder = None):
        assert holder is not None
        self.holder = holder

    def clone(self, holder, keys_to_skip = None):
        """Copy the formula just enough to be able to run a new simulation without modifying the original simulation."""
        new = empty_clone(self)
        new_dict = new.__dict__

        if keys_to_skip is None:
            keys_to_skip = set()
        keys_to_skip.add('holder')
        for key, value in self.__dict__.iteritems():
            if key not in keys_to_skip:
                new_dict[key] = value

        new_dict['holder'] = holder

        return new

    @property
    def real_formula(self):
        return self


class AbstractEntityToEntity(AbstractFormula):
    _variable_holder = None
    roles = None  # class attribute. When None the entity value is duplicated to each person belonging to entity.
    variable_name = None  # class attribute

    def clone(self, holder, keys_to_skip = None):
        """Copy the formula just enough to be able to run a new simulation without modifying the original simulation."""
        if keys_to_skip is None:
            keys_to_skip = set()
        keys_to_skip.add('_variable_holder')
        return super(AbstractEntityToEntity, self).clone(holder, keys_to_skip = keys_to_skip)

    def compute(self, period = None, requested_formulas_by_period = None):
        """Call the formula function (if needed) and return a dated holder containing its result."""
        assert period is not None
        holder = self.holder
        column = holder.column
        entity = holder.entity
        simulation = entity.simulation
        debug = simulation.debug
        debug_all = simulation.debug_all
        trace = simulation.trace

        if debug or trace:
            simulation.stack_trace.append(dict(
                input_legislation_infos = [],
                input_variables_infos = [],
                ))

        variable_holder = self.variable_holder
        variable_dated_holder = variable_holder.compute(period = period,
            requested_formulas_by_period = requested_formulas_by_period)
        output_period = variable_dated_holder.period

        array = self.transform(variable_dated_holder, roles = self.roles)
        if array.dtype != column.dtype:
            array = array.astype(column.dtype)

        if debug or trace:
            step = simulation.traceback.setdefault((column.name, output_period), {})
            step.update(simulation.stack_trace.pop())
            input_variables_infos = step['input_variables_infos']
            if not debug_all or trace:
                step['default_input_variables'] = has_only_default_input_variables = all(
                    np.all(input_holder.get_array(input_variable_period) == input_holder.column.default)
                    for input_holder, input_variable_period in (
                        (simulation.get_holder(input_variable_name), input_variable_period1)
                        for input_variable_name, input_variable_period1 in input_variables_infos
                        )
                    )
            step['is_computed'] = True
            if debug and (debug_all or not has_only_default_input_variables):
                log.info(u'<=> {}@{}<{}>({}) --> <{}>{}'.format(entity.key_plural, column.name, str(period),
                    simulation.stringify_input_variables_infos(input_variables_infos), stringify_array(array),
                    str(output_period)))

        dated_holder = holder.at_period(output_period)
        dated_holder.array = array
        return dated_holder

    def graph_parameters(self, edges, nodes, visited):
        """Recursively build a graph of formulas."""
        holder = self.holder
        column = holder.column
        variable_holder = self.variable_holder
        variable_holder.graph(edges, nodes, visited)
        edges.append({
            'from': variable_holder.column.name,
            'to': column.name,
            })

    @classmethod
    def set_dependencies(cls, column, tax_benefit_system):
        tax_benefit_system.consumers_by_variable_name.setdefault(cls.variable_name, set()).add(column.name)

    def to_json(self):
        cls = self.__class__
        comments = inspect.getcomments(cls)
        doc = inspect.getdoc(cls)
        source_lines, line_number = inspect.getsourcelines(cls)
        variable_holder = self.variable_holder
        variable_column = variable_holder.column
        variables_json = [collections.OrderedDict((
            ('entity', variable_holder.entity.key_plural),
            ('label', variable_column.label),
            ('name', variable_column.name),
            ))]
        return collections.OrderedDict((
            ('@type', cls.__bases__[0].__name__),
            ('comments', comments.decode('utf-8') if comments is not None else None),
            ('doc', doc.decode('utf-8') if doc is not None else None),
            ('line_number', line_number),
            ('module', inspect.getmodule(cls).__name__),
            ('source', ''.join(source_lines).decode('utf-8')),
            ('variables', variables_json),
            ))

    @property
    def variable_holder(self):
        # Note: This property is not precomputed at __init__ time, to ease the cloning of the formula.
        variable_holder = self._variable_holder
        if variable_holder is None:
            self._variable_holder = variable_holder = self.holder.entity.simulation.get_or_new_holder(
                self.variable_name)
        return variable_holder


class AbstractGroupedFormula(AbstractFormula):
    used_formula = None

    @property
    def real_formula(self):
        used_formula = self.used_formula
        if used_formula is None:
            return None
        return used_formula.real_formula


class DatedFormula(AbstractGroupedFormula):
    dated_formulas = None  # A list of dictionaries containing a formula jointly with start and stop instants
    dated_formulas_class = None  # Class attribute

    def __init__(self, holder = None):
        super(DatedFormula, self).__init__(holder = holder)

        self.dated_formulas = [
            dict(
                formula = dated_formula_class['formula_class'](holder = holder),
                start_instant = dated_formula_class['start_instant'],
                stop_instant = dated_formula_class['stop_instant'],
                )
            for dated_formula_class in self.dated_formulas_class
            ]
        assert self.dated_formulas

    def clone(self, holder, keys_to_skip = None):
        """Copy the formula just enough to be able to run a new simulation without modifying the original simulation."""
        if keys_to_skip is None:
            keys_to_skip = set()
        keys_to_skip.add('dated_formulas')
        new = super(DatedFormula, self).clone(holder, keys_to_skip = keys_to_skip)

        new.dated_formulas = [
            {
                key: value.clone(holder) if key == 'formula' else value
                for key, value in dated_formula.iteritems()
                }
            for dated_formula in self.dated_formulas
            ]

        return new

    def compute(self, period = None, requested_formulas_by_period = None):
        dated_holder = None
        stop_instant = period.stop
        for dated_formula in self.dated_formulas:
            if dated_formula['start_instant'] > stop_instant:
                break
            output_period = period.intersection(dated_formula['start_instant'], dated_formula['stop_instant'])
            if output_period is None:
                continue
            dated_holder = dated_formula['formula'].compute(period = output_period,
                requested_formulas_by_period = requested_formulas_by_period)
            if dated_holder.array is None:
                break
            self.used_formula = dated_formula['formula']
            return dated_holder

        holder = self.holder
        column = holder.column
        array = np.empty(holder.entity.count, dtype = column.dtype)
        array.fill(column.default)
        if dated_holder is None:
            dated_holder = holder.at_period(period)
        dated_holder.array = array
        return dated_holder

    def graph_parameters(self, edges, nodes, visited):
        """Recursively build a graph of formulas."""
        for dated_formula in self.dated_formulas:
            dated_formula['formula'].graph_parameters(edges, nodes, visited)

    @classmethod
    def set_dependencies(cls, column, tax_benefit_system):
        for dated_formula_class in cls.dated_formulas_class:
            dated_formula_class['formula_class'].set_dependencies(column, tax_benefit_system)

    def to_json(self):
        return collections.OrderedDict((
            ('@type', u'DatedFormula'),
            ('dated_formulas', [
                dict(
                    formula = dated_formula['formula'].to_json(),
                    start_instant = str(dated_formula['start_instant']),
                    stop_instant = str(dated_formula['stop_instant']),
                    )
                for dated_formula in self.dated_formulas
                ]),
            ))


class EntityToPerson(AbstractEntityToEntity):
    def transform(self, dated_holder, roles = None):
        """Cast an entity array to a persons array, setting only cells of persons having one of the given roles.

        When no roles are given, it means "all the roles" => every cell is set.
        """
        holder = self.holder
        persons = holder.entity
        assert persons.is_persons_entity

        entity = dated_holder.entity
        assert not entity.is_persons_entity
        array = dated_holder.array
        target_array = np.empty(persons.count, dtype = array.dtype)
        target_array.fill(dated_holder.column.default)
        entity_index_array = persons.holder_by_name[entity.index_for_person_variable_name].array
        if roles is None:
            roles = range(entity.roles_count)
        for role in roles:
            boolean_filter = persons.holder_by_name[entity.role_for_person_variable_name].array == role
            try:
                target_array[boolean_filter] = array[entity_index_array[boolean_filter]]
            except:
                log.error(u'An error occurred while transforming array for role {}[{}] in function {}'.format(
                    entity.key_singular, role, holder.column.name))
                raise
        return target_array


class PersonToEntity(AbstractEntityToEntity):
    operation = None

    def transform(self, dated_holder, roles = None):
        """Convert an array of persons to an array of non-person entities.

        When no roles are given, it means "all the roles".
        """
        holder = self.holder
        entity = holder.entity
        assert not entity.is_persons_entity

        persons = dated_holder.entity
        assert persons.is_persons_entity
        array = dated_holder.array

        target_array = np.empty(entity.count, dtype = array.dtype)
        target_array.fill(dated_holder.column.default)
        entity_index_array = persons.holder_by_name[entity.index_for_person_variable_name].array
        if roles is not None and len(roles) == 1:
            assert self.operation is None, 'Unexpected operation {} in formula {}'.format(self.operation,
                holder.column.name)
            role = roles[0]
            # TODO: Cache filter.
            boolean_filter = persons.holder_by_name[entity.role_for_person_variable_name].array == role
            try:
                target_array[entity_index_array[boolean_filter]] = array[boolean_filter]
            except:
                log.error(u'An error occurred while filtering array for role {}[{}] in function {}'.format(
                    entity.key_singular, role, holder.column.name))
                raise
        else:
            operation = self.operation
            assert operation in ('add', 'or'), 'Invalid operation {} in formula {}'.format(operation,
                holder.column.name)
            if roles is None:
                roles = range(entity.roles_count)
            target_array = np.zeros(entity.count,
                dtype = np.bool if operation == 'or' else array.dtype if array.dtype != np.bool else np.int16)
            for role in roles:
                # TODO: Cache filters.
                boolean_filter = persons.holder_by_name[entity.role_for_person_variable_name].array == role
                target_array[entity_index_array[boolean_filter]] += array[boolean_filter]

        return target_array


class SimpleFormula(AbstractFormula):
    _holder_by_variable_name = None
    function = None  # Class attribute. Overridden by subclasses
    legislation_accessor_by_name = None
    requires_legislation = False  # class attribute
    requires_period = False  # class attribute
    requires_reference_legislation = False  # class attribute
    requires_self = False  # class attribute
    variables_name = None  # class attribute

    def any_by_roles(self, array_or_dated_holder, entity = None, roles = None):
        holder = self.holder
        target_entity = holder.entity
        simulation = target_entity.simulation
        persons = simulation.persons
        if entity is None:
            entity = holder.entity
        else:
            assert entity in simulation.entity_by_key_singular, u"Unknown entity: {}".format(entity).encode('utf-8')
            entity = simulation.entity_by_key_singular[entity]
        assert not entity.is_persons_entity
        if isinstance(array_or_dated_holder, (holders.DatedHolder, holders.Holder)):
            assert array_or_dated_holder.entity.is_persons_entity
            array = array_or_dated_holder.array
        else:
            array = array_or_dated_holder
            assert isinstance(array, np.ndarray), u"Expected a holder or a Numpy array. Got: {}".format(array).encode(
                'utf-8')
            assert array.size == persons.count, u"Expected an array of size {}. Got: {}".format(persons.count,
                array.size)
        entity_index_array = persons.holder_by_name[entity.index_for_person_variable_name].array
        if roles is None:
            roles = range(entity.roles_count)
        target_array = np.zeros(entity.count, dtype = np.bool)
        for role in roles:
            # TODO Mettre les filtres en cache dans la simulation
            boolean_filter = persons.holder_by_name[entity.role_for_person_variable_name].array == role
            target_array[entity_index_array[boolean_filter]] += array[boolean_filter]
        return target_array

    def cast_from_entity_to_role(self, array_or_dated_holder, default = None, entity = None, role = None):
        """Cast an entity array to a persons array, setting only cells of persons having the given role."""
        assert isinstance(role, int)
        return self.cast_from_entity_to_roles(array_or_dated_holder, default = default, entity = entity, roles = [role])

    def cast_from_entity_to_roles(self, array_or_dated_holder, default = None, entity = None, roles = None):
        """Cast an entity array to a persons array, setting only cells of persons having one of the given roles.

        When no roles are given, it means "all the roles" => every cell is set.
        """
        holder = self.holder
        target_entity = holder.entity
        simulation = target_entity.simulation
        persons = simulation.persons
        if isinstance(array_or_dated_holder, (holders.DatedHolder, holders.Holder)):
            if entity is None:
                entity = array_or_dated_holder.entity
            else:
                assert entity in simulation.entity_by_key_singular, u"Unknown entity: {}".format(entity).encode('utf-8')
                entity = simulation.entity_by_key_singular[entity]
                assert entity == array_or_dated_holder.entity, \
                    u"""Holder entity "{}" and given entity "{}" don't match""".format(entity.key_plural,
                        array_or_dated_holder.entity.key_plural).encode('utf-8')
            array = array_or_dated_holder.array
            if default is None:
                default = array_or_dated_holder.column.default
        else:
            assert entity in simulation.entity_by_key_singular, u"Unknown entity: {}".format(entity).encode('utf-8')
            entity = simulation.entity_by_key_singular[entity]
            array = array_or_dated_holder
            assert isinstance(array, np.ndarray), u"Expected a holder or a Numpy array. Got: {}".format(array).encode(
                'utf-8')
            assert array.size == entity.count, u"Expected an array of size {}. Got: {}".format(entity.count,
                array.size)
            if default is None:
                default = 0
        assert not entity.is_persons_entity
        target_array = np.empty(persons.count, dtype = array.dtype)
        target_array.fill(default)
        entity_index_array = persons.holder_by_name[entity.index_for_person_variable_name].array
        if roles is None:
            roles = range(entity.roles_count)
        for role in roles:
            boolean_filter = persons.holder_by_name[entity.role_for_person_variable_name].array == role
            try:
                target_array[boolean_filter] = array[entity_index_array[boolean_filter]]
            except:
                log.error(u'An error occurred while transforming array for role {}[{}] in function {}'.format(
                    entity.key_singular, role, holder.column.name))
                raise
        return target_array

    def clone(self, holder, keys_to_skip = None):
        """Copy the formula just enough to be able to run a new simulation without modifying the original simulation."""
        if keys_to_skip is None:
            keys_to_skip = set()
        keys_to_skip.add('_holder_by_variable_name')
        return super(SimpleFormula, self).clone(holder, keys_to_skip = keys_to_skip)

    def compute(self, period = None, requested_formulas_by_period = None):
        """Call the formula function (if needed) and return a dated holder containing its result."""
        assert period is not None
        holder = self.holder
        column = holder.column
        entity = holder.entity
        simulation = entity.simulation
        debug = simulation.debug
        debug_all = simulation.debug_all
        trace = simulation.trace

        # Note: Don't compute intersection with column.start & column.end, because holder already does it:
        # output_period = output_period.intersection(periods.instant(column.start), periods.instant(column.end))
        # Note: Don't verify that the function result has already been computed, because this is the task of
        # holder.compute().

        # Ensure that method is not called several times for the same period (infinite loop).
        if requested_formulas_by_period is None:
            requested_formulas_by_period = {}
        period_or_none = None if column.is_permanent else period
        period_requested_formulas = requested_formulas_by_period.get(period_or_none)
        if period_requested_formulas is None:
            requested_formulas_by_period[period_or_none] = period_requested_formulas = set()
        else:
            assert self not in period_requested_formulas, \
                'Infinite loop in formula {}<{}>. Missing values for columns: {}'.format(
                    column.name,
                    period,
                    u', '.join(sorted(set(
                        u'{}<{}>'.format(requested_formula.holder.column.name, period1)
                        for period1, period_requested_formulas1 in requested_formulas_by_period.iteritems()
                        for requested_formula in period_requested_formulas1
                        ))).encode('utf-8'),
                    )
        period_requested_formulas.add(self)

        if debug or trace:
            simulation.stack_trace.append(dict(
                input_legislation_infos = [],
                input_variables_infos = [],
                ))

        try:
            output_period, array = self.function(simulation, period)
        except:
            log.error(u'An error occurred while calling function {}@{}<{}>()'.format(entity.key_plural, column.name,
                str(period)))
            raise
        assert output_period[1] <= period[1] <= output_period.stop, \
            u"Function {}@{}<{}>() --> <{}>{} returns an output period that doesn't include start instant of" \
            u"requested period".format(entity.key_plural, column.name, str(period), str(output_period),
                stringify_array(array)).encode('utf-8')
        assert isinstance(array, np.ndarray), \
            u"Function {}@{}<{}>() --> <{}>{} doesn't return a numpy array".format(
                entity.key_plural, column.name, str(period), str(output_period), array).encode('utf-8')
        assert array.size == entity.count, \
            u"Function {}@{}<{}>() --> <{}>{} returns an array of size {}, but size {} is expected for {}".format(
                entity.key_plural, column.name, str(period), str(output_period), stringify_array(array),
                array.size, entity.count, entity.key_singular).encode('utf-8')
        if debug:
            try:
                # cf http://stackoverflow.com/questions/6736590/fast-check-for-nan-in-numpy
                if np.isnan(np.min(array)):
                    nan_count = np.count_nonzero(np.isnan(array))
                    raise NaNCreationError(u"Function {}@{}<{}>() --> <{}>{} returns {} NaN value(s)".format(
                        entity.key_plural, column.name, str(period), str(output_period), stringify_array(array),
                        nan_count).encode('utf-8'))
            except TypeError:
                pass
        if array.dtype != column.dtype:
            array = array.astype(column.dtype)

        if debug or trace:
            step = simulation.traceback.setdefault((column.name, output_period), {})
            step.update(simulation.stack_trace.pop())
            input_variables_infos = step['input_variables_infos']
            if not debug_all or trace:
                step['default_input_variables'] = has_only_default_input_variables = all(
                    np.all(input_holder.get_array(input_variable_period) == input_holder.column.default)
                    for input_holder, input_variable_period in (
                        (simulation.get_holder(input_variable_name), input_variable_period1)
                        for input_variable_name, input_variable_period1 in input_variables_infos
                        )
                    )
            step['is_computed'] = True
            if debug and (debug_all or not has_only_default_input_variables):
                log.info(u'<=> {}@{}<{}>({}) --> <{}>{}'.format(entity.key_plural, column.name, str(period),
                    simulation.stringify_input_variables_infos(input_variables_infos), str(output_period),
                    stringify_array(array)))

        dated_holder = holder.at_period(output_period)
        dated_holder.array = array
        period_requested_formulas.remove(self)
        return dated_holder

    def filter_role(self, array_or_dated_holder, default = None, entity = None, role = None):
        """Convert a persons array to an entity array, copying only cells of persons having the given role."""
        holder = self.holder
        simulation = holder.entity.simulation
        persons = simulation.persons
        if entity is None:
            entity = holder.entity
        else:
            assert entity in simulation.entity_by_key_singular, u"Unknown entity: {}".format(entity).encode('utf-8')
            entity = simulation.entity_by_key_singular[entity]
        assert not entity.is_persons_entity
        if isinstance(array_or_dated_holder, (holders.DatedHolder, holders.Holder)):
            assert array_or_dated_holder.entity.is_persons_entity
            array = array_or_dated_holder.array
            if default is None:
                default = array_or_dated_holder.column.default
        else:
            array = array_or_dated_holder
            assert isinstance(array, np.ndarray), u"Expected a holder or a Numpy array. Got: {}".format(array).encode(
                'utf-8')
            assert array.size == persons.count, u"Expected an array of size {}. Got: {}".format(persons.count,
                array.size)
            if default is None:
                default = 0
        entity_index_array = persons.holder_by_name[entity.index_for_person_variable_name].array
        assert isinstance(role, int)
        target_array = np.empty(entity.count, dtype = array.dtype)
        target_array.fill(default)
        boolean_filter = persons.holder_by_name[entity.role_for_person_variable_name].array == role
        try:
            target_array[entity_index_array[boolean_filter]] = array[boolean_filter]
        except:
            log.error(u'An error occurred while filtering array for role {}[{}] in function {}'.format(
                entity.key_singular, role, holder.column.name))
            raise
        return target_array

    def get_law_instant(self, output_period, law_path):
        """Return the instant required for a node of the legislation used by the formula.

        By default, the instant of a legislation node is the start instant of the output period of the formula.

        Override this method when needing different instants for legislation nodes.
        """
        return output_period[1]

    def get_variable_period(self, output_period, variable_name):
        """Return the period required for an input variable used by the formula.

        By default, the period of an input variable is the output period of the formula.

        Override this method for input variables with different periods.
        """
        return output_period

    def graph_parameters(self, edges, nodes, visited):
        """Recursively build a graph of formulas."""
        holder = self.holder
        column = holder.column
        for variable_holder in self.holder_by_variable_name.itervalues():
            variable_holder.graph(edges, nodes, visited)
            edges.append({
                'from': variable_holder.column.name,
                'to': column.name,
                })

    @property
    def holder_by_variable_name(self):
        # Note: This property is not precomputed at __init__ time, to ease the cloning of the formula.
        holder_by_variable_name = self._holder_by_variable_name
        if holder_by_variable_name is None:
            self._holder_by_variable_name = holder_by_variable_name = collections.OrderedDict()
            simulation = self.holder.entity.simulation
            for variable_name in self.variables_name:
                clean_variable_name = variable_name[:-len('_holder')] \
                    if variable_name.endswith('_holder') \
                    else variable_name
                holder_by_variable_name[variable_name] = simulation.get_or_new_holder(clean_variable_name)
        return holder_by_variable_name

    @classmethod
    def set_dependencies(cls, column, tax_benefit_system):
        for variable_name in cls.variables_name:
            clean_variable_name = variable_name[:-len('_holder')] \
                if variable_name.endswith('_holder') \
                else variable_name
            tax_benefit_system.consumers_by_variable_name.setdefault(clean_variable_name, set()).add(column.name)

    def split_by_roles(self, array_or_dated_holder, default = None, entity = None, roles = None):
        """dispatch a persons array to several entity arrays (one for each role)."""
        holder = self.holder
        simulation = holder.entity.simulation
        persons = simulation.persons
        if entity is None:
            entity = holder.entity
        else:
            assert entity in simulation.entity_by_key_singular, u"Unknown entity: {}".format(entity).encode('utf-8')
            entity = simulation.entity_by_key_singular[entity]
        assert not entity.is_persons_entity
        if isinstance(array_or_dated_holder, (holders.DatedHolder, holders.Holder)):
            assert array_or_dated_holder.entity.is_persons_entity
            array = array_or_dated_holder.array
            if default is None:
                default = array_or_dated_holder.column.default
        else:
            array = array_or_dated_holder
            assert isinstance(array, np.ndarray), u"Expected a holder or a Numpy array. Got: {}".format(array).encode(
                'utf-8')
            assert array.size == persons.count, u"Expected an array of size {}. Got: {}".format(persons.count,
                array.size)
            if default is None:
                default = 0
        entity_index_array = persons.holder_by_name[entity.index_for_person_variable_name].array
        if roles is None:
            # To ensure that existing formulas don't fail, ensure there is always at least 11 roles.
            # roles = range(entity.roles_count)
            roles = range(max(entity.roles_count, 11))
        target_array_by_role = {}
        for role in roles:
            target_array_by_role[role] = target_array = np.empty(entity.count, dtype = array.dtype)
            target_array.fill(default)
            boolean_filter = persons.holder_by_name[entity.role_for_person_variable_name].array == role
            try:
                target_array[entity_index_array[boolean_filter]] = array[boolean_filter]
            except:
                log.error(u'An error occurred while filtering array for role {}[{}] in function {}'.format(
                    entity.key_singular, role, holder.column.name))
                raise
        return target_array_by_role

    def sum_by_entity(self, array_or_dated_holder, entity = None, roles = None):
        holder = self.holder
        target_entity = holder.entity
        simulation = target_entity.simulation
        persons = simulation.persons
        if entity is None:
            entity = holder.entity
        else:
            assert entity in simulation.entity_by_key_singular, u"Unknown entity: {}".format(entity).encode('utf-8')
            entity = simulation.entity_by_key_singular[entity]
        assert not entity.is_persons_entity
        if isinstance(array_or_dated_holder, (holders.DatedHolder, holders.Holder)):
            assert array_or_dated_holder.entity.is_persons_entity
            array = array_or_dated_holder.array
        else:
            array = array_or_dated_holder
            assert isinstance(array, np.ndarray), u"Expected a holder or a Numpy array. Got: {}".format(array).encode(
                'utf-8')
            assert array.size == persons.count, u"Expected an array of size {}. Got: {}".format(persons.count,
                array.size)
        entity_index_array = persons.holder_by_name[entity.index_for_person_variable_name].array
        if roles is None:
            roles = range(entity.roles_count)
        target_array = np.zeros(entity.count, dtype = array.dtype if array.dtype != np.bool else np.int16)
        for role in roles:
            # TODO: Mettre les filtres en cache dans la simulation
            boolean_filter = persons.holder_by_name[entity.role_for_person_variable_name].array == role
            target_array[entity_index_array[boolean_filter]] += array[boolean_filter]
        return target_array

    def to_json(self):
        function = self.function
        comments = inspect.getcomments(function)
        doc = inspect.getdoc(function)
        source_lines, line_number = inspect.getsourcelines(function)
        source = textwrap.dedent(''.join(source_lines).decode('utf-8'))
        variables_json = []
        for variable_name, variable_holder in self.holder_by_variable_name.iteritems():
            variable_column = variable_holder.column
            variables_json.append(collections.OrderedDict((
                ('entity', variable_holder.entity.key_plural),
                ('label', variable_column.label),
                ('name', variable_column.name),
                )))
        return collections.OrderedDict((
            ('@type', u'SimpleFormula'),
            ('comments', comments.decode('utf-8') if comments is not None else None),
            ('doc', doc.decode('utf-8') if doc is not None else None),
            ('line_number', line_number),
            ('module', inspect.getmodule(function).__name__),
            ('source', source),
            ('variables', variables_json),
            ))


# Formulas Generators


class ConversionColumnMetaclass(type):
    """The metaclass of ConversionColumn classes: It generates a column instead of a formula ConversionColumn class."""
    def __new__(cls, name, bases, attributes):
        """Return a column containing a casting formula, built from ConversionColumn class definition."""
        assert len(bases) == 1, bases
        base_class = bases[0]
        if base_class is object:
            # Do nothing when creating classes DatedFormulaColumn, SimpleFormulaColumn, etc.
            return super(ConversionColumnMetaclass, cls).__new__(cls, name, bases, attributes)

        # Extract attributes.

        formula_class = attributes.pop('formula_class', base_class.formula_class)
        assert issubclass(formula_class, AbstractFormula), formula_class

        cerfa_field = attributes.pop('cerfa_field', None)
        if cerfa_field is not None:
            cerfa_field = unicode(cerfa_field)

        doc = attributes.pop('__doc__', None)

        entity_class = attributes.pop('entity_class')

        name = unicode(name)
        label = attributes.pop('label', None)
        label = name if label is None else unicode(label)

        url = attributes.pop('url', None)
        if url is not None:
            url = unicode(url)

        variable = attributes.pop('variable')
        assert isinstance(variable, columns.Column)

        # Build formula class and column from extracted attributes.

        formula_class_attributes = dict(
            __module__ = attributes.pop('__module__'),
            )
        if doc is not None:
            formula_class_attributes['__doc__'] = doc

        role = attributes.pop('role', None)
        roles = attributes.pop('roles', None)
        if role is None:
            if roles is not None:
                assert isinstance(roles, (list, tuple)) and all(isinstance(role, int) for role in roles)
        else:
            assert isinstance(role, int)
            assert roles is None
            roles = [role]
        if roles is not None:
            formula_class_attributes['roles'] = roles

        formula_class_attributes['variable_name'] = variable.name

        if issubclass(formula_class, EntityToPerson):
            assert entity_class.is_persons_entity
            column = variable.empty_clone()
        else:
            assert issubclass(formula_class, PersonToEntity)

            assert not entity_class.is_persons_entity

            if roles is None or len(roles) > 1:
                operation = attributes.pop('operation')
                assert operation in ('add', 'or'), 'Invalid operation: {}'.format(operation)
                formula_class_attributes['operation'] = operation

                if operation == 'add':
                    if variable.__class__ is columns.BoolCol:
                        column = columns.IntCol()
                    else:
                        column = variable.empty_clone()
                else:
                    assert operation == 'or'
                    column = variable.empty_clone()
            else:
                column = variable.empty_clone()

        # Ensure that all attributes defined in ConversionColumn class are used.
        assert not attributes, 'Unexpected attributes in definition of class {}: {}'.format(name,
            ', '.join(attributes.iterkeys()))

        formula_class = type(name.encode('utf-8'), (formula_class,), formula_class_attributes)

        # Fill column attributes.
        if cerfa_field is not None:
            column.cerfa_field = cerfa_field
        if variable.end is not None:
            column.end = variable.end
        column.entity = entity_class.symbol  # Obsolete: To remove once build_..._couple() functions are no more used.
        column.entity_key_plural = entity_class.key_plural
        column.formula_class = formula_class
        if variable.is_permanent:
            column.is_permanent = True
        column.label = label
        column.name = name
        if variable.start is not None:
            column.start = variable.start
        if url is not None:
            column.url = url

        return column


class FormulaColumnMetaclass(type):
    """The metaclass of FormulaColumn classes: It generates a column instead of a formula FormulaColumn class."""
    def __new__(cls, name, bases, attributes):
        """Return a column containing a formula, built from FormulaColumn class definition."""
        assert len(bases) == 1, bases
        base_class = bases[0]
        if base_class is object:
            # Do nothing when creating classes DatedFormulaColumn, SimpleFormulaColumn, etc.
            return super(FormulaColumnMetaclass, cls).__new__(cls, name, bases, attributes)

        # Extract attributes.

        cerfa_field = attributes.pop('cerfa_field', None)
        if cerfa_field is not None:
            cerfa_field = unicode(cerfa_field)

        column = attributes.pop('column')
        if not isinstance(column, columns.Column):
            column = column()
            assert isinstance(column, columns.Column)

        doc = attributes.pop('__doc__', None)

        entity_class = attributes.pop('entity_class')

        formula_class = attributes.pop('formula_class', base_class.formula_class)
        assert issubclass(formula_class, AbstractFormula), formula_class

        is_permanent = attributes.pop('is_permanent', False)
        assert is_permanent in (False, True), is_permanent

        get_law_instant = attributes.pop('get_law_instant', None)
        get_output_period = attributes.pop('get_output_period', None)
        get_variable_period = attributes.pop('get_variable_period', None)

        name = unicode(name)
        label = attributes.pop('label', None)
        label = name if label is None else unicode(label)

        start_date = attributes.pop('start_date', None)
        if start_date is not None:
            assert isinstance(start_date, datetime.date)

        stop_date = attributes.pop('stop_date', None)
        if stop_date is not None:
            assert isinstance(stop_date, datetime.date)

        url = attributes.pop('url', None)
        if url is not None:
            url = unicode(url)

        # Build formula class and column from extracted attributes.

        formula_class_attributes = dict(
            __module__ = attributes.pop('__module__'),
            )
        if doc is not None:
            formula_class_attributes['__doc__'] = doc

        if issubclass(formula_class, DatedFormula):
            dated_formulas_class = []
            for function_name, function in attributes.copy().iteritems():
                start_instant = getattr(function, 'start_instant', UnboundLocalError)
                if start_instant is UnboundLocalError:
                    # Function is not dated (and may not even be a function). Skip it.
                    continue
                stop_instant = function.stop_instant
                if stop_instant is not None:
                    assert start_instant <= stop_instant, 'Invalid instant interval for function {}: {} - {}'.format(
                        function_name, start_instant, stop_instant)

                dated_formula_class_attributes = formula_class_attributes.copy()
                dated_formula_class_attributes['function'] = function
                if get_law_instant is not None:
                    dated_formula_class_attributes['get_law_instant'] = get_law_instant
                if get_output_period is not None:
                    dated_formula_class_attributes['get_output_period'] = get_output_period
                if get_variable_period is not None:
                    dated_formula_class_attributes['get_variable_period'] = get_variable_period
                dated_formula_class = type(name.encode('utf-8'), (SimpleFormula,), dated_formula_class_attributes)

                del attributes[function_name]
                dated_formulas_class.append(dict(
                    formula_class = dated_formula_class,
                    start_instant = start_instant,
                    stop_instant = stop_instant,
                    ))
            # Sort dated formulas by start instant and add missing stop instants.
            dated_formulas_class.sort(key = lambda dated_formula_class: dated_formula_class['start_instant'])
            for dated_formula_class, next_dated_formula_class in itertools.izip(dated_formulas_class,
                    itertools.islice(dated_formulas_class, 1, None)):
                if dated_formula_class['stop_instant'] is None:
                    dated_formula_class['stop_instant'] = next_dated_formula_class['start_instant'].offset(-1, 'day')
                else:
                    assert dated_formula_class['stop_instant'] < next_dated_formula_class['start_instant'], \
                        "Dated formulas overlap: {} & {}".format(dated_formula_class, next_dated_formula_class)

            formula_class_attributes['dated_formulas_class'] = dated_formulas_class
        else:
            assert issubclass(formula_class, SimpleFormula), formula_class
            function = attributes.pop('function')
            assert function is not None
            formula_class_attributes['function'] = function
            if get_law_instant is not None:
                formula_class_attributes['get_law_instant'] = get_law_instant
            if get_output_period is not None:
                formula_class_attributes['get_output_period'] = get_output_period
            if get_variable_period is not None:
                formula_class_attributes['get_variable_period'] = get_variable_period

        # Ensure that all attributes defined in FormulaColumn class are used.
        assert not attributes, 'Unexpected attributes in definition of class {}: {}'.format(name,
            ', '.join(attributes.iterkeys()))

        formula_class = type(name.encode('utf-8'), (formula_class,), formula_class_attributes)

        # Fill column attributes.
        if cerfa_field is not None:
            column.cerfa_field = cerfa_field
        if stop_date is not None:
            column.end = stop_date
        column.entity = entity_class.symbol  # Obsolete: To remove once build_..._couple() functions are no more used.
        column.entity_key_plural = entity_class.key_plural
        column.formula_class = formula_class
        if is_permanent:
            column.is_permanent = True
        column.label = label
        column.name = name
        if start_date is not None:
            column.start = start_date
        if url is not None:
            column.url = url

        return column


class DatedFormulaColumn(object):
    """Syntactic sugar to generate a DatedFormula class and fill its column"""
    __metaclass__ = FormulaColumnMetaclass
    formula_class = DatedFormula


class EntityToPersonColumn(object):
    """Syntactic sugar to generate an EntityToPerson class and fill its column"""
    __metaclass__ = ConversionColumnMetaclass
    formula_class = EntityToPerson


class PersonToEntityColumn(object):
    """Syntactic sugar to generate an PersonToEntity class and fill its column"""
    __metaclass__ = ConversionColumnMetaclass
    formula_class = PersonToEntity


class SimpleFormulaColumn(object):
    """Syntactic sugar to generate a SimpleFormula class and fill its column"""
    __metaclass__ = FormulaColumnMetaclass
    formula_class = SimpleFormula


def build_dated_formula(name = None, dated_functions = None, column = None, entity_class_by_symbol = None,
        replace = False):
    # Obsolete: Use FormulaColumn classes and reference_formula decorator instead."""
    assert isinstance(name, basestring), name
    name = unicode(name)
    assert isinstance(dated_functions, list), dated_functions
    assert column.function is None

    dated_formulas_class = []
    for dated_function in dated_functions:
        assert isinstance(dated_function, dict), dated_function

        formula_class = type(
            name.encode('utf-8'),
            (SimpleFormula,),
            dict(
                function = staticmethod(dated_function['function']),
                # Use a year period starting at beginning of month.
                get_output_period = lambda self, period: period.start.offset('first-of', 'month').period('year'),
                ),
            )
        dated_formulas_class.append(dict(
            formula_class = formula_class,
            start_instant = periods.instant(dated_function['start']),
            stop_instant = periods.instant(dated_function['end']),
            ))
    dated_formulas_class.sort(key = lambda dated_formula_class: dated_formula_class['start_instant'])

    entity_class = entity_class_by_symbol[column.entity]
    column.entity_key_plural = entity_class.key_plural
    column.formula_class = formula_class = type(name.encode('utf-8'), (DatedFormula,), dict(
        dated_formulas_class = dated_formulas_class,
        ))
    if column.label is None:
        column.label = name
    assert column.name is None
    column.name = name

    entity_column_by_name = entity_class.column_by_name
    if not replace:
        assert name not in entity_column_by_name, name
    entity_column_by_name[name] = column


def build_simple_formula(name = None, column = None, entity_class_by_symbol = None, replace = False):
    # Obsolete: Use FormulaColumn classes and reference_formula decorator instead."""
    assert isinstance(name, basestring), name
    name = unicode(name)

    entity_class = entity_class_by_symbol[column.entity]
    column.entity_key_plural = entity_class.key_plural
    column.formula_class = type(name.encode('utf-8'), (SimpleFormula,), dict(
        function = staticmethod(column.function),
        # Use a year period starting at beginning of month.
        get_output_period = lambda self, period: period.start.offset('first-of', 'month').period('year'),
        ))
    del column.function
    if column.label is None:
        column.label = name
    assert column.name is None
    column.name = name

    entity_column_by_name = entity_class.column_by_name
    if not replace:
        assert name not in entity_column_by_name, name
    entity_column_by_name[name] = column


def dated_function(start = None, stop = None):
    """Function decorator used to give start & stop instants to a method of a function in class DatedFormulaColumn."""
    def dated_function_decorator(function):
        function.start_instant = periods.instant(start)
        function.stop_instant = periods.instant(stop)
        return function

    return dated_function_decorator


def make_reference_formula_decorator(entity_class_by_symbol = None):
    assert isinstance(entity_class_by_symbol, dict)

    def reference_formula_decorator(column):
        """Class decorator used to declare a formula to the relevant entity class."""
        assert isinstance(column, columns.Column)
        assert column.formula_class is not None

        entity_class = entity_class_by_symbol[column.entity]
        entity_column_by_name = entity_class.column_by_name
        name = column.name
        assert name not in entity_column_by_name, name
        entity_column_by_name[name] = column

        return column

    return reference_formula_decorator
