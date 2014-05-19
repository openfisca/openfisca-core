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
import inspect
import logging

import numpy as np

from . import accessors, holders


log = logging.getLogger(__name__)


class AbstractFormula(object):
    holder = None

    def __init__(self, holder = None):
        assert holder is not None
        self.holder = holder


class AlternativeFormula(AbstractFormula):
    alternative_formulas = None
    alternative_formulas_constructor = None  # Class attribute. List of formulas sorted by descending preference

    def __init__(self, holder = None):
        super(AlternativeFormula, self).__init__(holder = holder)

        self.alternative_formulas = [
            alternative_formula_constructor(holder = holder)
            for alternative_formula_constructor in self.alternative_formulas_constructor
            ]

    def calculate(self, lazy = False, requested_formulas = None):
        holder = self.holder
        column = holder.column

        if requested_formulas is None:
            requested_formulas = set()
        elif lazy:
            if self in requested_formulas:
                return holder.array
        else:
            assert self not in requested_formulas, 'Infinite loop in formula {}. Missing values for columns: {}'.format(
                column.name,
                u', '.join(sorted(set(
                    requested_formula.holder.column.name
                    for requested_formula in requested_formulas
                    ))).encode('utf-8'),
                )

        if holder.array is not None:
            return holder.array
#        if holder.disabled:
#            return holder.array

        requested_formulas.add(self)
        for alternative_formula in self.alternative_formulas:
            # Caution: Note that requested_formulas are copied below.
            array = alternative_formula.calculate(lazy = True, requested_formulas = requested_formulas.copy())
            if array is not None:
                holder.array = array
                requested_formulas.remove(self)
                return array
        if lazy:
            requested_formulas.remove(self)
            return None
        # No alternative has an existing array => Calculate array using first alternative.
        # TODO: Imagine a better strategy.
        alternative_formula = self.alternative_formulas[0]
        holder.array = array = alternative_formula.calculate(lazy = False, requested_formulas = requested_formulas)
        requested_formulas.remove(self)
        return array

    def graph_parameters(self, edges, nodes, visited):
        """Recursively build a graph of formulas."""
        for alternative_formula in self.alternative_formulas:
            alternative_formula.graph_parameters(edges, nodes, visited)

    @classmethod
    def set_dependencies(cls, column, column_by_name):
        for alternative_formula_constructor in cls.alternative_formulas_constructor:
            alternative_formula_constructor.set_dependencies(column, column_by_name)

    def to_json(self):
        return collections.OrderedDict((
            ('@type', u'AlternativeFormula'),
            ('alternative_formulas', [
                alternative_formula.to_json()
                for alternative_formula in self.alternative_formulas
                ]),
            ))


class DatedFormula(AbstractFormula):
    dated_formulas = None # A list of dictionnary containing a formula jointly with a start date and an end date
    dated_formulas_class = None  # Class attribute.

    def __init__(self, holder = None):
        super(DatedFormula, self).__init__(holder = holder)

        self.dated_formulas = [
            dict(
                end = dated_formula_class['end'],
                formula = dated_formula_class['formula_class'](holder = holder),
                start = dated_formula_class['start'],
                )
            for dated_formula_class in self.dated_formulas_class
            ]

    def calculate(self, lazy = False, requested_formulas = None):
        holder = self.holder
        column = holder.column

        if requested_formulas is None:
            requested_formulas = set()
        elif lazy:
            if self in requested_formulas:
                return holder.array
        else:
            assert self not in requested_formulas, 'Infinite loop in formula {}. Missing values for columns: {}'.format(
                column.name,
                u', '.join(sorted(set(
                    requested_formula.holder.column.name
                    for requested_formula in requested_formulas
                    ))).encode('utf-8'),
                )

        if holder.array is not None:
            return holder.array
#        if holder.disabled:
#            return holder.array

        entity = holder.entity
        simulation = entity.simulation
        datesim = simulation.compact_legislation.datesim
        requested_formulas.add(self)
        for dated_formula in self.dated_formulas:
            if dated_formula['start'] <= datesim <= dated_formula['end']:
                array = dated_formula['formula'].calculate(lazy = lazy, requested_formulas = requested_formulas)
                if array is not None:
                    holder.array = array
                    requested_formulas.remove(self)
                    return array

        holder.array = np.empty(entity.count, dtype = column.dtype)
        holder.array.fill(column.default)
        requested_formulas.remove(self)
        return holder.array

    def graph_parameters(self, edges, nodes, visited):
        """Recursively build a graph of formulas."""
        for dated_formula in self.dated_formulas:
            dated_formula['formula'].graph_parameters(edges, nodes, visited)

    @classmethod
    def set_dependencies(cls, column, column_by_name):
        for dated_formula_class in cls.dated_formulas_class:
            dated_formula_class['formula_class'].set_dependencies(column, column_by_name)

    def to_json(self):
        return collections.OrderedDict((
            ('@type', u'DatedFormula'),
            ('dated_formulas', [
                dict(
                    end = dated_formula['end'].isoformat(),
                    formula = dated_formula['formula'].to_json(),
                    start = dated_formula['start'].isoformat(),
                    )
                for dated_formula in self.dated_formulas
                ]),
            ))


class SelectFormula(AbstractFormula):
    formula_by_main_variable = None
    formula_constructor_by_main_variable = None  # Class attribute. List of formulas sorted by descending preference

    def __init__(self, holder = None):
        super(SelectFormula, self).__init__(holder = holder)

        self.formula_by_main_variable = collections.OrderedDict(
            (main_variable, formula_constructor(holder = holder))
            for main_variable, formula_constructor in self.formula_constructor_by_main_variable.iteritems()
            )

    def calculate(self, lazy = False, requested_formulas = None):
        holder = self.holder
        column = holder.column

        if requested_formulas is None:
            requested_formulas = set()
        elif lazy:
            if self in requested_formulas:
                return holder.array
        else:
            assert self not in requested_formulas, 'Infinite loop in formula {}. Missing values for columns: {}'.format(
                column.name,
                u', '.join(sorted(set(
                    requested_formula.holder.column.name
                    for requested_formula in requested_formulas
                    ))).encode('utf-8'),
                )

        if holder.array is not None:
            return holder.array
#        if holder.disabled:
#            return holder.array

        entity = holder.entity
        simulation = entity.simulation
        requested_formulas.add(self)
        for main_variable, formula in self.formula_by_main_variable.iteritems():
            main_array = simulation.calculate(main_variable, lazy = True, requested_formulas = requested_formulas)
            if main_array is not None:
                selected_formula = formula
                break
        else:
            selected_formula = self.formula_by_main_variable.values()[0]
        holder.array = array = selected_formula.calculate(lazy = lazy, requested_formulas = requested_formulas)
        requested_formulas.remove(self)
        return array

    def graph_parameters(self, edges, nodes, visited):
        """Recursively build a graph of formulas."""
        for formula in self.formula_by_main_variable.itervalues():
            formula.graph_parameters(edges, nodes, visited)

    @classmethod
    def set_dependencies(cls, column, column_by_name):
        for formula_constructor in cls.formula_constructor_by_main_variable.itervalues():
            formula_constructor.set_dependencies(column, column_by_name)

    def to_json(self):
        return collections.OrderedDict((
            ('@type', u'SelectFormula'),
            ('formula_by_main_variable', collections.OrderedDict(
                (main_variable, formula.to_json())
                for main_variable, formula in self.formula_by_main_variable.iteritems()
                )),
            ))


class SimpleFormula(AbstractFormula):
    function = None  # Class attribute. Overridden by subclasses
    holder_by_parameter = None
    legislation_accessor_by_name = None
    parameters = None  # class attribute
    requires_default_legislation = False  # class attribute
    requires_legislation = False  # class attribute
    requires_self = False  # class attribute

    def __init__(self, holder = None):
        super(SimpleFormula, self).__init__(holder = holder)

        column = holder.column
        entity = holder.entity
        simulation = entity.simulation
        self.holder_by_parameter = holder_by_parameter = collections.OrderedDict()
        for parameter in self.parameters:
            clean_parameter = parameter[:-len('_holder')] if parameter.endswith('_holder') else parameter
            holder_by_parameter[parameter] = parameter_holder = simulation.get_or_new_holder(clean_parameter)

    def any_by_roles(self, array_or_holder, entity = None, roles = None):
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
        target_array = np.zeros(entity.count, dtype = np.bool)
        for role in roles:
            # TODO Mettre les filtres en cache dans la simulation
            boolean_filter = persons.holder_by_name['qui' + entity.symbol].array == role
            target_array[entity_index_array[boolean_filter]] += array[boolean_filter]
        return target_array

    def calculate(self, lazy = False, requested_formulas = None):
        holder = self.holder
        column = holder.column

        if requested_formulas is None:
            requested_formulas = set()
        elif lazy:
            if self in requested_formulas:
                return holder.array
        else:
            assert self not in requested_formulas, 'Infinite loop in formula {}. Missing values for columns: {}'.format(
                column.name,
                u', '.join(sorted(set(
                    requested_formula.holder.column.name
                    for requested_formula in requested_formulas
                    ))).encode('utf-8'),
                )

        entity = holder.entity
        simulation = entity.simulation

        if holder.array is not None:
            return holder.array
#        if holder.disabled:
#            return holder.array

        requested_formulas.add(self)
        required_parameters = set(self.holder_by_parameter.iterkeys()).union(
            (self.legislation_accessor_by_name or {}).iterkeys())
        arguments = {}
        if simulation.debug and not simulation.debug_all or simulation.trace:
            has_only_default_arguments = True
        for parameter, parameter_holder in self.holder_by_parameter.iteritems():
            parameter_array = parameter_holder.calculate(lazy = lazy, requested_formulas = requested_formulas)
            if parameter_array is None:
                # A parameter is missing in lazy mode, formula can not be calculated yet.
                assert lazy
                requested_formulas.remove(self)
                return None
            # When parameter ends with "_holder" suffix, use holder as argument instead of its array.
            # It is a hack until we use static typing annotations of Python 3 (cf PEP 3107).
            arguments[parameter] = parameter_holder if parameter.endswith('_holder') else parameter_holder.array
            if (simulation.debug and not simulation.debug_all or simulation.trace) and has_only_default_arguments \
                    and np.any(parameter_array != parameter_holder.column.default):
                has_only_default_arguments = False

        if self.requires_default_legislation:
            required_parameters.add('_defaultP')
            arguments['_defaultP'] = simulation.default_compact_legislation
        if self.requires_legislation:
            required_parameters.add('_P')
            arguments['_P'] = simulation.compact_legislation
        if self.requires_self:
            required_parameters.add('self')
            arguments['self'] = self
        if self.legislation_accessor_by_name is not None:
            for name, legislation_accessor in self.legislation_accessor_by_name.iteritems():
                # TODO: Also handle simulation.default_compact_legislation
                arguments[name] = legislation_accessor(simulation.compact_legislation, default = None)

        provided_parameters = set(arguments.keys())
        assert provided_parameters == required_parameters, 'Formula {} requires missing parameters : {}'.format(
            u', '.join(sorted(required_parameters - provided_parameters)).encode('utf-8'))

        try:
            array = self.function(**arguments)
        except:
            log.error(u'An error occurred while calling function {}@{}({})'.format(entity.key_plural, column.name,
                self.get_arguments_str()))
            raise
        assert isinstance(array, np.ndarray), u"Function {}@{}({}) doesn't return a numpy array, but: {}".format(
            entity.key_plural, column.name, self.get_arguments_str(), array).encode('utf-8')
        assert array.size == entity.count, \
            u"Function {}@{}({}) returns an array of size {}, but size {} is expected for {}".format(entity.key_plural,
            column.name, self.get_arguments_str(), array.size, entity.count, entity.key_singular).encode('utf-8')
        if array.dtype != column.dtype:
            array = array.astype(column.dtype)
        if simulation.debug and (simulation.debug_all or not has_only_default_arguments):
            log.info(u'<=> {}@{}({}) --> {}'.format(entity.key_plural, column.name, self.get_arguments_str(), array))
        holder.array = array
        if simulation.trace:
            simulation.traceback[column.name].update(dict(
                default_arguments = has_only_default_arguments,
                is_computed = True,
                ))
        requested_formulas.remove(self)
        return array

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
                default = array_or_holder.column.default
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

    @classmethod
    def extract_parameters(cls):
        function = cls.function
        code = function.__code__
        defaults = function.__defaults__ or ()
        if defaults:
            cls.legislation_accessor_by_name = {}
            for name, default in zip(code.co_varnames[code.co_argcount - len(defaults):code.co_argcount], defaults):
                assert isinstance(default, accessors.Accessor), 'Unexpected defaut parameter: {} = {}'.format(name,
                    default)
                cls.legislation_accessor_by_name[name] = default
        cls.parameters = parameters = list(code.co_varnames[:code.co_argcount - len(defaults)])
        # Check whether default legislation is used by function.
        if '_defaultP' in parameters:
            cls.requires_default_legislation = True
            parameters.remove('_defaultP')
        # Check whether current legislation is used by function.
        if '_P' in parameters:
            cls.requires_legislation = True
            parameters.remove('_P')
        # Check whether function uses self (aka formula).
        if 'self' in parameters:
            cls.requires_self = True
            parameters.remove('self')

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
                default = array_or_holder.column.default
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

    def get_arguments_str(self):
        return u', '.join(
            u'{} = {}@{}'.format(parameter, parameter_holder.entity.key_plural, unicode(parameter_holder.array))
            for parameter, parameter_holder in self.holder_by_parameter.iteritems()
            )

    def graph_parameters(self, edges, nodes, visited):
        """Recursively build a graph of formulas."""
        holder = self.holder
        column = holder.column
        entity = holder.entity
        simulation = entity.simulation
        for parameter_holder in self.holder_by_parameter.itervalues():
            parameter_holder.graph(edges, nodes, visited)
            edges.append({
                'from': parameter_holder.column.name,
                'to': column.name,
                })

    @classmethod
    def set_dependencies(cls, column, column_by_name):
        for parameter in cls.parameters:
            clean_parameter = parameter[:-len('_holder')] if parameter.endswith('_holder') else parameter
            parameter_column = column_by_name[clean_parameter]
            if parameter_column.consumers is None:
                parameter_column.consumers = set()
            parameter_column.consumers.add(column.name)

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
                default = array_or_holder.column.default
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
        target_array = np.zeros(entity.count, dtype = array.dtype if array.dtype != np.bool else np.int16)
        for role in roles:
            # TODO Mettre les filtres en cache dans la simulation
            boolean_filter = persons.holder_by_name['qui' + entity.symbol].array == role
            target_array[entity_index_array[boolean_filter]] += array[boolean_filter]
        return target_array

    def to_json(self):
        function = self.function
        comments = inspect.getcomments(function)
        doc = inspect.getdoc(function)
        parameters_json = []
        for parameter, parameter_holder in self.holder_by_parameter.iteritems():
            parameter_column = parameter_holder.column
            parameters_json.append(collections.OrderedDict((
                ('entity', parameter_holder.entity.key_plural),
                ('label', parameter_column.label),
                ('name', parameter_column.name),
                )))
        source_lines, line_number = inspect.getsourcelines(function)
        return collections.OrderedDict((
            ('@type', u'SimpleFormula'),
            ('comments', comments.decode('utf-8') if comments is not None else None),
            ('doc', doc.decode('utf-8') if doc is not None else None),
            ('line_number', line_number),
            ('module', inspect.getmodule(function).__name__),
            ('parameters', parameters_json),
            ('source', ''.join(source_lines).decode('utf-8')),
            ))
