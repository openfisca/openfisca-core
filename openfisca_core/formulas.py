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

from . import accessors, columns, holders, periods


log = logging.getLogger(__name__)


# Exceptions


class NaNCreationError(Exception):
    def __init__(self, column_name, entity, index):
        self.column_name = column_name
        self.entity = entity
        self.index = index

    def __str__(self):
        return repr("{} NaN value(s) are present in {} variable {}".format(
            len(self.index),
            self.entity.key_singular,
            self.column_name,
            ))


# Formulas


class AbstractFormula(object):
    holder = None
    period_unit = None  # class method

    def __init__(self, holder = None):
        assert holder is not None
        self.holder = holder


class AbstractGroupedFormula(AbstractFormula):
    used_formula = None

    @property
    def real_formula(self):
        used_formula = self.used_formula
        if used_formula is None:
            return None
        return used_formula.real_formula


class AlternativeFormula(AbstractGroupedFormula):
    alternative_formulas = None
    alternative_formulas_constructor = None  # Class attribute. List of formulas sorted by descending preference

    def __init__(self, holder = None):
        super(AlternativeFormula, self).__init__(holder = holder)

        self.alternative_formulas = [
            alternative_formula_constructor(holder = holder)
            for alternative_formula_constructor in self.alternative_formulas_constructor
            ]

    def compute(self, lazy = False, period = None, requested_formulas_by_period = None):
        holder = self.holder
        column = holder.column
        entity = holder.entity
        simulation = entity.simulation
        if period is None:
            period = simulation.period

        if requested_formulas_by_period is None:
            requested_formulas_by_period = {}
        period_or_none = None if column.is_period_invariant else period
        period_requested_formulas = requested_formulas_by_period.get(period_or_none)
        if period_requested_formulas is None:
            requested_formulas_by_period[period_or_none] = period_requested_formulas = set()
        elif lazy:
            if self in period_requested_formulas:
                return holder.at_period(period)
        else:
            assert self not in period_requested_formulas, \
                'Infinite loop in formula {}. Missing values for columns: {}'.format(
                    column.name,
                    u', '.join(sorted(set(
                        requested_formula.holder.column.name
                        for requested_formula in period_requested_formulas
                        ))).encode('utf-8'),
                    )

        dated_holder = holder.at_period(period)
        if dated_holder.array is not None:
            return dated_holder

        period_requested_formulas.add(self)
        for alternative_formula in self.alternative_formulas:
            # Copy requested_formulas_by_period.
            new_requested_formulas_by_period = dict(
                (period, period_requested_formulas1.copy())
                for period, period_requested_formulas1 in requested_formulas_by_period.iteritems()
                )
            dated_holder = alternative_formula.compute(lazy = True, period = period,
                requested_formulas_by_period = new_requested_formulas_by_period)
            if dated_holder is not None:
                self.used_formula = alternative_formula
                holder.set_array(period, dated_holder.array)
                period_requested_formulas.remove(self)
                return holder.at_period(period)
        if lazy:
            period_requested_formulas.remove(self)
            return None
        # No alternative has an existing array => Compute array using first alternative.
        # TODO: Imagine a better strategy.
        alternative_formula = self.alternative_formulas[0]
        self.used_formula = alternative_formula
        dated_holder = alternative_formula.compute(lazy = False, period = period,
            requested_formulas_by_period = requested_formulas_by_period)
        holder.set_array(period, dated_holder.array)
        period_requested_formulas.remove(self)
        return holder.at_period(period)

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


class DatedFormula(AbstractGroupedFormula):
    dated_formulas = None  # A list of dictionaries containing a formula jointly with a start date and an end date
    dated_formulas_class = None  # Class attribute

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

    def compute(self, lazy = False, period = None, requested_formulas_by_period = None):
        holder = self.holder
        column = holder.column
        entity = holder.entity
        simulation = entity.simulation
        if period is None:
            period = simulation.period

        if requested_formulas_by_period is None:
            requested_formulas_by_period = {}
        period_or_none = None if column.is_period_invariant else period
        period_requested_formulas = requested_formulas_by_period.get(period_or_none)
        if period_requested_formulas is None:
            requested_formulas_by_period[period_or_none] = period_requested_formulas = set()
        elif lazy:
            if self in period_requested_formulas:
                return holder.at_period(period)
        else:
            assert self not in period_requested_formulas, \
                'Infinite loop in formula {}. Missing values for columns: {}'.format(
                    column.name,
                    u', '.join(sorted(set(
                        requested_formula.holder.column.name
                        for requested_formula in period_requested_formulas
                        ))).encode('utf-8'),
                    )

        dated_holder = holder.at_period(period)
        if dated_holder.array is not None:
            return dated_holder

        assert periods.unit(period) == u'year'
        period_date = periods.date(period)  # TODO: Handle different start & stop dates.

        period_requested_formulas.add(self)
        for dated_formula in self.dated_formulas:
            if dated_formula['start'] <= period_date <= dated_formula['end']:
                dated_holder = dated_formula['formula'].compute(lazy = lazy, period = period,
                    requested_formulas_by_period = requested_formulas_by_period)
                if dated_holder is not None:
                    self.used_formula = dated_formula['formula']
                    holder.set_array(period, dated_holder.array)
                    period_requested_formulas.remove(self)
                    return holder.at_period(period)

        array = np.empty(entity.count, dtype = column.dtype)
        array.fill(column.default)
        holder.set_array(period, array)
        period_requested_formulas.remove(self)
        return holder.at_period(period)

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


class SelectFormula(AbstractGroupedFormula):
    formula_by_main_variable = None
    formula_constructor_by_main_variable = None  # Class attribute. List of formulas sorted by descending preference

    def __init__(self, holder = None):
        super(SelectFormula, self).__init__(holder = holder)

        self.formula_by_main_variable = collections.OrderedDict(
            (main_variable, formula_constructor(holder = holder))
            for main_variable, formula_constructor in self.formula_constructor_by_main_variable.iteritems()
            )

    def compute(self, lazy = False, period = None, requested_formulas_by_period = None):
        holder = self.holder
        column = holder.column
        entity = holder.entity
        simulation = entity.simulation
        if period is None:
            period = simulation.period

        if requested_formulas_by_period is None:
            requested_formulas_by_period = {}
        period_or_none = None if column.is_period_invariant else period
        period_requested_formulas = requested_formulas_by_period.get(period_or_none)
        if period_requested_formulas is None:
            requested_formulas_by_period[period_or_none] = period_requested_formulas = set()
        elif lazy:
            if self in period_requested_formulas:
                return holder.at_period(period)
        else:
            assert self not in period_requested_formulas, \
                'Infinite loop in formula {}. Missing values for columns: {}'.format(
                    column.name,
                    u', '.join(sorted(set(
                        requested_formula.holder.column.name
                        for requested_formula in period_requested_formulas
                        ))).encode('utf-8'),
                    )

        dated_holder = holder.at_period(period)
        if dated_holder.array is not None:
            return dated_holder

        period_requested_formulas.add(self)
        for main_variable, formula in self.formula_by_main_variable.iteritems():
            main_dated_holder = simulation.compute(main_variable, lazy = True, period = period,
                requested_formulas_by_period = requested_formulas_by_period)
            if main_dated_holder is not None:
                selected_formula = formula
                break
        else:
            selected_formula = self.formula_by_main_variable.values()[0]
        self.used_formula = selected_formula
        dated_holder = selected_formula.compute(lazy = lazy, period = period,
            requested_formulas_by_period = requested_formulas_by_period)
        holder.set_array(period, dated_holder.array)
        period_requested_formulas.remove(self)
        return holder.at_period(period)

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
    holder_by_variable_name = None
    legislation_accessor_by_name = None
    requires_legislation = False  # class attribute
    requires_period = False  # class attribute
    requires_reference_legislation = False  # class attribute
    requires_self = False  # class attribute
    variables_name = None  # class attribute

    def __init__(self, holder = None):
        super(SimpleFormula, self).__init__(holder = holder)

        entity = holder.entity
        simulation = entity.simulation
        self.holder_by_variable_name = holder_by_variable_name = collections.OrderedDict()
        for variable_name in self.variables_name:
            clean_variable_name = variable_name[:-len('_holder')] \
                if variable_name.endswith('_holder') \
                else variable_name
            holder_by_variable_name[variable_name] = simulation.get_or_new_holder(clean_variable_name)

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
        if isinstance(array_or_holder, (holders.DatedHolder, holders.Holder)):
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
        if isinstance(array_or_holder, (holders.DatedHolder, holders.Holder)):
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

    def compute(self, lazy = False, period = None, requested_formulas_by_period = None):
        """Call the formula function (if needed) and return a dated holder containing its result."""
        holder = self.holder
        column = holder.column
        entity = holder.entity
        simulation = entity.simulation
        if period is None:
            period = simulation.period

        if requested_formulas_by_period is None:
            requested_formulas_by_period = {}
        period_or_none = None if column.is_period_invariant else period
        period_requested_formulas = requested_formulas_by_period.get(period_or_none)
        if period_requested_formulas is None:
            requested_formulas_by_period[period_or_none] = period_requested_formulas = set()
        elif lazy:
            if self in period_requested_formulas:
                return holder.at_period(period)
        else:
            assert self not in period_requested_formulas, \
                'Infinite loop in formula {}. Missing values for columns: {}'.format(
                    column.name,
                    u', '.join(sorted(set(
                        requested_formula.holder.column.name
                        for requested_formula in period_requested_formulas
                        ))).encode('utf-8'),
                    )

        dated_holder = holder.at_period(period)
        if dated_holder.array is not None:
            return dated_holder

        period_requested_formulas.add(self)
        required_parameters = set(self.holder_by_variable_name.iterkeys()).union(
            (self.legislation_accessor_by_name or {}).iterkeys())
        arguments = {}
        if simulation.debug and not simulation.debug_all or simulation.trace:
            has_only_default_arguments = True
        for variable_name, variable_holder in self.holder_by_variable_name.iteritems():
            variable_period = self.get_variable_period(period, variable_name)
            variable_dated_holder = variable_holder.compute(lazy = lazy, period = variable_period,
                requested_formulas_by_period = requested_formulas_by_period)
            if variable_dated_holder is None:
                # A variable is missing in lazy mode, formula can not be computed yet.
                assert lazy
                period_requested_formulas.remove(self)
                return None
            # When variable_name ends with "_holder" suffix, use holder as argument instead of its array.
            # It is a hack until we use static typing annotations of Python 3 (cf PEP 3107).
            arguments[variable_name] = variable_holder.at_period(variable_period) \
                if variable_name.endswith('_holder') \
                else variable_holder.array
            if (simulation.debug and not simulation.debug_all or simulation.trace) and has_only_default_arguments \
                    and np.any(variable_dated_holder.array != variable_holder.column.default):
                has_only_default_arguments = False

        if self.requires_legislation:
            required_parameters.add('_P')
            arguments['_P'] = simulation.get_compact_legislation(period)
        if self.requires_reference_legislation:
            required_parameters.add('_defaultP')
            arguments['_defaultP'] = simulation.get_reference_compact_legislation(period)
        if self.requires_self:
            required_parameters.add('self')
            arguments['self'] = self
        if self.requires_period:
            required_parameters.add('period')
            arguments['period'] = period
        if self.legislation_accessor_by_name is not None:
            for name, legislation_accessor in self.legislation_accessor_by_name.iteritems():
                # TODO: Also handle simulation.get_reference_compact_legislation(...).
                arguments[name] = legislation_accessor(
                    simulation.get_compact_legislation(self.get_law_period(period, legislation_accessor.path)),
                    default = None,
                    )

        provided_parameters = set(arguments.keys())
        assert provided_parameters == required_parameters, 'Formula {} requires missing parameters : {}'.format(
            u', '.join(sorted(required_parameters - provided_parameters)).encode('utf-8'))

        try:
            result = self.function(**arguments)
        except:
            log.error(u'An error occurred while calling function {}@{}({})'.format(entity.key_plural, column.name,
                self.get_arguments_str()))
            raise
        if isinstance(result, holders.DatedHolder):
            assert result.holder is self.holder, u"Function {}@{}({}) doesn't return its own holder, but: {}".format(
                entity.key_plural, column.name, self.get_arguments_str(), result).encode('utf-8')
            dated_holder = result
        else:
            dated_holder = self.set_result_array(period, result)

        if simulation.debug and (simulation.debug_all or not has_only_default_arguments):
            log.info(u'<=> {}@{}({}) --> {}'.format(entity.key_plural, column.name, self.get_arguments_str(),
                dated_holder.array))
        if simulation.trace:
            simulation.traceback[column.name].update(dict(
                default_arguments = has_only_default_arguments,
                is_computed = True,
                ))
        period_requested_formulas.remove(self)

        return dated_holder

    @classmethod
    def extract_variables_name(cls):
        function = cls.function
        code = function.__code__
        defaults = function.__defaults__ or ()
        if defaults:
            cls.legislation_accessor_by_name = {}
            for name, default in zip(code.co_varnames[code.co_argcount - len(defaults):code.co_argcount], defaults):
                assert isinstance(default, accessors.Accessor), 'Unexpected defaut parameter: {} = {}'.format(name,
                    default)
                cls.legislation_accessor_by_name[name] = default
        cls.variables_name = variables_name = list(code.co_varnames[:code.co_argcount - len(defaults)])
        # Check whether default legislation is used by function.
        if '_defaultP' in variables_name:
            cls.requires_reference_legislation = True
            variables_name.remove('_defaultP')
        # Check whether current legislation is used by function.
        if '_P' in variables_name:
            cls.requires_legislation = True
            variables_name.remove('_P')
        if 'period' in variables_name:
            cls.requires_period = True
            variables_name.remove('period')
        # Check whether function uses self (aka formula).
        if 'self' in variables_name:
            # Don't require self for a method (it will have a value for self when it is bound).
            if not inspect.ismethod(function):
                cls.requires_self = True
            variables_name.remove('self')

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
        if isinstance(array_or_holder, (holders.DatedHolder, holders.Holder)):
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
            u'{} = {}@{}'.format(variable_name, variable_holder.entity.key_plural, unicode(variable_holder.array))
            for variable_name, variable_holder in self.holder_by_variable_name.iteritems()
            )

    def get_law_period(self, period, law_path):
        """Return the period required for a node of the legislation used by the formula.

        By default, the period of a legislation node is the same as the requested period.
        Override this method for legislation nodes with different periods.
        """
        return period

    def get_variable_period(self, period, variable_name):
        """Return the period required for an input variable used by the formula.

        By default, the period of an input variable is the same as the requested period.
        Override this method for input variables with different periods.
        """
        return period

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
    def real_formula(self):
        return self

    @classmethod
    def set_dependencies(cls, column, column_by_name):
        for variable_name in cls.variables_name:
            clean_variable_name = variable_name[:-len('_holder')] \
                if variable_name.endswith('_holder') \
                else variable_name
            variable_column = column_by_name[clean_variable_name]
            if variable_column.consumers is None:
                variable_column.consumers = set()
            variable_column.consumers.add(column.name)

    def set_result_array(self, period, array):
        holder = self.holder
        column = holder.column
        entity = holder.entity
        simulation = entity.simulation

        assert isinstance(array, np.ndarray), u"Function {}@{}({}) doesn't return a numpy array, but: {}".format(
            entity.key_plural, column.name, self.get_arguments_str(), array).encode('utf-8')
        assert array.size == entity.count, \
            u"Function {}@{}({}) returns an array of size {}, but size {} is expected for {}".format(entity.key_plural,
            column.name, self.get_arguments_str(), array.size, entity.count, entity.key_singular).encode('utf-8')

        if not simulation.debug:
            try:
                # cf http://stackoverflow.com/questions/6736590/fast-check-for-nan-in-numpy
                if np.isnan(np.min(array)):
                    raise NaNCreationError(column.name, entity, np.arange(len(array))[np.isnan(array)])
            except TypeError:
                pass

        if array.dtype != column.dtype:
            array = array.astype(column.dtype)

        dated_holder = holder.at_period(period)
        dated_holder.array = array
        return dated_holder

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
        if isinstance(array_or_holder, (holders.DatedHolder, holders.Holder)):
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
        if isinstance(array_or_holder, (holders.DatedHolder, holders.Holder)):
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
            # TODO: Mettre les filtres en cache dans la simulation
            boolean_filter = persons.holder_by_name['qui' + entity.symbol].array == role
            target_array[entity_index_array[boolean_filter]] += array[boolean_filter]
        return target_array

    def to_json(self):
        function = self.function
        comments = inspect.getcomments(function)
        doc = inspect.getdoc(function)
        source_lines, line_number = inspect.getsourcelines(function)
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
            ('source', ''.join(source_lines).decode('utf-8')),
            ('variables', variables_json),
            ))


# Formulas couple builders


def build_alternative_formula_couple(name = None, functions = None, column = None, entity_class_by_symbol = None):
    assert isinstance(name, basestring), name
    name = unicode(name)
    assert isinstance(functions, list), functions
    assert column.function is None

    alternative_formulas_constructor = []
    for function in functions:
        formula_class = type(name.encode('utf-8'), (SimpleFormula,), dict(
            function = staticmethod(function),
            period_unit = u'year',
            ))
        formula_class.extract_variables_name()
        alternative_formulas_constructor.append(formula_class)
    column.formula_constructor = formula_class = type(name.encode('utf-8'), (AlternativeFormula,), dict(
        alternative_formulas_constructor = alternative_formulas_constructor,
        period_unit = u'year',
        ))
    if column.label is None:
        column.label = name
    assert column.name is None
    column.name = name

    entity_column_by_name = entity_class_by_symbol[column.entity].column_by_name
    assert name not in entity_column_by_name, name
    entity_column_by_name[name] = column

    return (name, column)


def build_dated_formula_couple(name = None, dated_functions = None, column = None, entity_class_by_symbol = None,
                               replace = False):
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
                period_unit = u'year',
                ),
            )
        formula_class.extract_variables_name()
        dated_formulas_class.append(dict(
            end = dated_function['end'],
            formula_class = formula_class,
            start = dated_function['start'],
            ))

    column.formula_constructor = formula_class = type(name.encode('utf-8'), (DatedFormula,), dict(
        dated_formulas_class = dated_formulas_class,
        period_unit = u'year',
        ))
    if column.label is None:
        column.label = name
    assert column.name is None
    column.name = name

    entity_column_by_name = entity_class_by_symbol[column.entity].column_by_name
    if not replace:
        assert name not in entity_column_by_name, name
    entity_column_by_name[name] = column

    return (name, column)


def build_select_formula_couple(name = None, main_variable_function_couples = None, column = None,
                                entity_class_by_symbol = None):
    assert isinstance(name, basestring), name
    name = unicode(name)
    assert isinstance(main_variable_function_couples, list), main_variable_function_couples
    assert column.function is None

    formula_constructor_by_main_variable = collections.OrderedDict()
    for main_variable, function in main_variable_function_couples:
        formula_class = type(name.encode('utf-8'), (SimpleFormula,), dict(
            function = staticmethod(function),
            period_unit = u'year',
            ))
        formula_class.extract_variables_name()
        formula_constructor_by_main_variable[main_variable] = formula_class
    column.formula_constructor = formula_class = type(name.encode('utf-8'), (SelectFormula,), dict(
        formula_constructor_by_main_variable = formula_constructor_by_main_variable,
        period_unit = u'year',
        ))
    if column.label is None:
        column.label = name
    assert column.name is None
    column.name = name

    entity_column_by_name = entity_class_by_symbol[column.entity].column_by_name
    assert name not in entity_column_by_name, name
    entity_column_by_name[name] = column

    return (name, column)


def build_simple_formula_couple(name = None, column = None, entity_class_by_symbol = None, replace = False):
    assert isinstance(name, basestring), name
    name = unicode(name)

    column.formula_constructor = formula_class = type(name.encode('utf-8'), (SimpleFormula,), dict(
        function = staticmethod(column.function),
        period_unit = u'year',
        ))
    formula_class.extract_variables_name()
    del column.function
    if column.label is None:
        column.label = name
    assert column.name is None
    column.name = name

    entity_column_by_name = entity_class_by_symbol[column.entity].column_by_name
    if not replace:
        assert name not in entity_column_by_name, name
    entity_column_by_name[name] = column

    return (name, column)


def reference_formula(prestation_by_name = None):
    """Decorator used to declare a formula defined in reference tax benefit system."""
    def reference_formula_decorator(formula_class):
        formula_class.extract_variables_name()

        entity_class = formula_class.entity_class
        formula_class.name = name = unicode(formula_class.__name__)
        formula_class.label = label = name if formula_class.label is None else unicode(formula_class.label)
        assert formula_class.period_unit in (u'month', u'year'), formula_class.period_unit

        column = formula_class.column
        if not isinstance(column, columns.Column):
            column = column()
            assert isinstance(column, columns.Column)
        column.entity = entity_class.symbol
        column.label = label
        column.formula_constructor = formula_class
        column.name = name

        entity_column_by_name = entity_class.column_by_name
        assert name not in entity_column_by_name, name
        entity_column_by_name[name] = column

        assert name not in prestation_by_name, name
        prestation_by_name[name] = column

        return formula_class

    return reference_formula_decorator
