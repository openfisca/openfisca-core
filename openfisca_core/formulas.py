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


import logging

import numpy as np

from . import holders


log = logging.getLogger(__name__)


class AbstractFormula(object):
    holder = None

    def __init__(self, holder = None):
        assert holder is not None
        self.holder = holder


class AbstractSimpleFormula(AbstractFormula):
    parameters = None
    requires_default_legislation = False
    requires_legislation = False
    requires_self = False

    def __init__(self, holder = None):
        super(AbstractSimpleFormula, self).__init__(holder = holder)

        function = self.calculate
        code = function.__code__
        self.parameters = parameters = list(code.co_varnames[:code.co_argcount])
        # Check whether default legislation is used by function.
        if '_defaultP' in parameters:
            self.requires_default_legislation = True
            parameters.remove('_defaultP')
        # Check whether current legislation is used by function.
        if '_P' in parameters:
            self.requires_legislation = True
            parameters.remove('_P')
        # Check whether function uses self (aka formula).
        if 'self' in parameters:
            self.requires_self = True
            parameters.remove('self')

    def __call__(self, requested_columns_name = None):
        holder = self.holder
        column = holder.column
        entity = holder.entity
        simulation = entity.simulation

        if requested_columns_name is None:
            requested_columns_name = set()
        else:
            assert column.name not in requested_columns_name, 'Infinite loop. Missing values for columns: {}'.format(
                u', '.join(sorted(requested_columns_name)).encode('utf-8'))

        if holder.array is not None:
            return holder
#        if holder.disabled:
#            return holder

        requested_columns_name.add(holder.column.name)
        required_parameters = set(self.parameters)
        arguments = {}
        arguments_holder = []
        for parameter in self.parameters:
            clean_parameter = parameter[:-len('_holder')] if parameter.endswith('_holder') else parameter
            argument_holder = simulation.compute(clean_parameter, requested_columns_name = requested_columns_name)
            arguments_holder.append(argument_holder)
            # When parameter ends with "_holder" suffix, use holder as argument instead of its array.
            # It is a hack until we use static typing annotations of Python 3 (cf PEP 3107).
            arguments[parameter] = argument_holder if parameter.endswith('_holder') else argument_holder.array

        if self.requires_default_legislation:
            required_parameters.add('_defaultP')
            arguments['_defaultP'] = simulation.default_compact_legislation
        if self.requires_legislation:
            required_parameters.add('_P')
            arguments['_P'] = simulation.compact_legislation
        if self.requires_self:
            required_parameters.add('self')
            arguments['self'] = self

        provided_parameters = set(arguments.keys())
        assert provided_parameters == required_parameters, 'Formula {} requires missing parameters : {}'.format(
            u', '.join(sorted(required_parameters - provided_parameters)).encode('utf-8'))

        if simulation.debug:
            log.info(u'--> {}@{}({})'.format(entity.key_plural, column.name,
                get_arguments_str(arguments_holder)))
        try:
            array = self.calculate(**arguments)
        except:
            log.error(u'An error occurred while calling function {}@{}({})'.format(entity.key_plural, column.name,
                get_arguments_str(arguments_holder)))
            raise
        assert isinstance(array, np.ndarray), u"Function {}@{}({}) doesn't return a numpy array, but: {}".format(
            entity.key_plural, column.name, get_arguments_str(arguments_holder), array).encode('utf-8')
        assert array.size == entity.count, \
            u"Function {}@{}({}) returns an array of size {}, but size {} is expected for {}".format(entity.key_plural,
            column.name, get_arguments_str(arguments_holder), array.size, entity.count,entity.key_singular).encode(
            'utf-8')
        if array.dtype != column._dtype:
            array = array.astype(column._dtype)
        if simulation.debug:
            log.info(u'<-- {}@{}: {}'.format(entity.key_plural, column.name, array))
        holder.array = array
        requested_columns_name.remove(holder.column.name)
        return holder

    def any_by_roles(self, array_or_holder, entity = None, roles = None):
        return self.sum_by_entity(array_or_holder, entity = entity, roles = roles)

    def cast_from_entity_to_role(self, array_or_holder, default = None, entity = None, role = None):
        """Cast an entity array to a persons array, setting only cells of persons having the given role."""
        assert isinstance(role, int)
        return self.cast_from_entity_to_roles(array_or_holder, default = default, entity = entity, roles = [role])

    def cast_from_entity_to_roles(self, array_or_holder, default = None, entity = None, roles = None):
        """Cast an entity array to a persons array, setting only cells of persons having one of the given roles.

        When no roles are given, it means "all the roles" => every cell is set.
        """
        holder = self.holder
        target_entity = holder.entity
        simulation = target_entity.simulation
        persons = simulation.persons
        if isinstance(array_or_holder, holders.Holder):
            if entity is None:
                entity = array_or_holder.entity
            else:
                assert entity in simulation.entity_by_key_singular, u"Unknown entity: {}".format(entity).encode('utf-8')
                entity = simulation.entity_by_key_singular[entity]
                assert entity == array_or_holder.entity, u"""Holder entity "{}" and given entity "{}" don't match""" \
                    .format(entity.key_plural, array_or_holder.entity.key_plural).encode('utf-8')
            array = array_or_holder.array
            if default is None:
                default = array_or_holder.column._default
        else:
            assert entity in simulation.entity_by_key_singular, u"Unknown entity: {}".format(entity).encode('utf-8')
            entity = simulation.entity_by_key_singular[entity]
            array = array_or_holder
            assert isinstance(array, np.ndarray), u"Expected a holder or a Numpy array. Got: {}".format(array).encode(
                'utf-8')
            assert array.size == entity.count, u"Expected an array of size {}. Got: {}".format(entity.count,
                array.size)
            if default is None:
                default = 0
        assert not entity.is_persons_entity
        target_array = np.empty(persons.count, dtype = array.dtype)
        target_array.fill(default)
        entity_index_array = persons.holder_by_name['id' + entity.symbol].array
        if roles is None:
            roles = range(entity.roles_count)
        for role in roles:
            boolean_filter = persons.holder_by_name['qui' + entity.symbol].array == role
            try:
                target_array[boolean_filter] = array[entity_index_array[boolean_filter]]
            except:
                log.error(u'An error occurred while transforming array for role {}[{}] in function {}'.format(
                    entity.key_singular, role, holder.column.name))
                raise
        return target_array

    def filter_role(self, array_or_holder, default = None, entity = None, role = None):
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
        if isinstance(array_or_holder, holders.Holder):
            assert array_or_holder.entity.is_persons_entity
            array = array_or_holder.array
            if default is None:
                default = array_or_holder.column._default
        else:
            array = array_or_holder
            assert isinstance(array, np.ndarray), u"Expected a holder or a Numpy array. Got: {}".format(array).encode(
                'utf-8')
            assert array.size == persons.count, u"Expected an array of size {}. Got: {}".format(persons.count,
                array.size)
            if default is None:
                default = 0
        entity_index_array = persons.holder_by_name['id' + entity.symbol].array
        assert isinstance(role, int)
        target_array = np.empty(entity.count, dtype = array.dtype)
        target_array.fill(default)
        boolean_filter = persons.holder_by_name['qui' + entity.symbol].array == role
        try:
            target_array[entity_index_array[boolean_filter]] = array[boolean_filter]
        except:
            log.error(u'An error occurred while filtering array for role {}[{}] in function {}'.format(
                entity.key_singular, role, holder.column.name))
            raise
        return target_array

    def split_by_roles(self, array_or_holder, default = None, entity = None, roles = None):
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
        if isinstance(array_or_holder, holders.Holder):
            assert array_or_holder.entity.is_persons_entity
            array = array_or_holder.array
            if default is None:
                default = array_or_holder.column._default
        else:
            array = array_or_holder
            assert isinstance(array, np.ndarray), u"Expected a holder or a Numpy array. Got: {}".format(array).encode(
                'utf-8')
            assert array.size == persons.count, u"Expected an array of size {}. Got: {}".format(persons.count,
                array.size)
            if default is None:
                default = 0
        entity_index_array = persons.holder_by_name['id' + entity.symbol].array
        if roles is None:
            # To ensure that existing formulas don't fail, ensure there is always at least 11 roles.
            # roles = range(entity.roles_count)
            roles = range(max(entity.roles_count, 11))
        target_array_by_role = {}
        for role in roles:
            target_array_by_role[role] = target_array = np.empty(entity.count, dtype = array.dtype)
            target_array.fill(default)
            boolean_filter = persons.holder_by_name['qui' + entity.symbol].array == role
            try:
                target_array[entity_index_array[boolean_filter]] = array[boolean_filter]
            except:
                log.error(u'An error occurred while filtering array for role {}[{}] in function {}'.format(
                    entity.key_singular, role, holder.column.name))
                raise
        return target_array_by_role

    def sum_by_entity(self, array_or_holder, entity = None, roles = None):
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
        if isinstance(array_or_holder, holders.Holder):
            assert array_or_holder.entity.is_persons_entity
            array = array_or_holder.array
        else:
            array = array_or_holder
            assert isinstance(array, np.ndarray), u"Expected a holder or a Numpy array. Got: {}".format(array).encode(
                'utf-8')
            assert array.size == persons.count, u"Expected an array of size {}. Got: {}".format(persons.count,
                array.size)
        entity_index_array = persons.holder_by_name['id' + entity.symbol].array
        if roles is None:
            roles = range(entity.roles_count)
        target_array = np.zeros(entity.count, dtype = array.dtype)
        for role in roles:
            # TODO Mettre les filtres en cache dans la simulation
            boolean_filter = persons.holder_by_name['qui' + entity.symbol].array == role
            target_array[entity_index_array[boolean_filter]] += array[boolean_filter]
        return target_array


def get_arguments_str(arguments_holder):
    return u', '.join(
        u'{} = {}@{}'.format(argument_holder.column.name, argument_holder.entity.key_plural,
            unicode(argument_holder.array))
        for argument_holder in arguments_holder
        )
