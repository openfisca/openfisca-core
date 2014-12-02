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


"""Parsers for formula-specific Abstract Syntax Trees"""


from __future__ import division

import ast
import collections
import inspect
import itertools
import textwrap

import numpy as np
from openfisca_core import conv


class Array(object):
    column = None
    data_type = None
    entity_key_plural = None
    is_argument = False
    operation = None

    def __init__(self, column = None, data_type = None, entity_key_plural = None, is_argument = False,
            operation = None):
        if column is not None:
            self.column = column
            assert column.dtype == data_type, str((column.dtype, data_type))
            assert column.entity_key_plural == entity_key_plural
        if data_type is not None:
            self.data_type = data_type
        if entity_key_plural is not None:
            self.entity_key_plural = entity_key_plural
        if is_argument:
            self.is_argument = True
        if operation is not None:
            self.operation = operation


class ArrayLength(object):
    array = None

    def __init__(self, array):
        if array is not None:
            self.array = array


class BinaryOperation(object):
    left = None
    operator = None  # AST operator
    right = None

    def __init__(self, left = None, operator = None, right = None):
        if left is not None:
            self.left = left
        if operator is not None:
            self.operator = operator
        if right is not None:
            self.right = right


class Continue(object):
    pass


class Date(object):
    pass


class DatedHolder(object):
    column = None
    data_type = None
    entity_key_plural = None
    is_argument = False

    def __init__(self, column = None, data_type = None, entity_key_plural = None, is_argument = False):
        if column is not None:
            self.column = column
            assert column.dtype == data_type, str((column.dtype, data_type))
            assert column.entity_key_plural == entity_key_plural
        if data_type is not None:
            self.data_type = data_type
        if entity_key_plural is not None:
            self.entity_key_plural = entity_key_plural
        if is_argument:
            self.is_argument = True


class DateTime64(object):
    pass


class Enum(object):
    pass


class Entity(object):
    pass


class EntityToEntity(object):
    keyword_arguments = None
    method_name = None
    named_arguments = None
    positional_arguments = None
    star_arguments = None

    def __init__(self, keyword_arguments = None, method_name = None, named_arguments = None,
            positional_arguments = None, star_arguments = None):
        if keyword_arguments is not None:
            self.keyword_arguments = keyword_arguments
        if method_name is not None:
            self.method_name = method_name
        if named_arguments is not None:
            self.named_arguments = named_arguments
        if positional_arguments is not None:
            self.positional_arguments = positional_arguments
        if star_arguments is not None:
            self.star_arguments = star_arguments


class FunctionCall(object):
    definition = None
    value_by_name = None

    def __init__(self, definition = None):
        assert isinstance(definition, FunctionDefinition)
        self.definition = definition
        self.value_by_name = {}

    def get_value_by_name(self, name, default = UnboundLocalError, state = None):
        value = self.value_by_name.get(name, UnboundLocalError)
        if value is UnboundLocalError:
            container = self.definition.container
            if container is not None:
                return container.get_value_by_name(name, default = default, state = state)
        if value is UnboundLocalError:
            raise KeyError("Undefined value for {}".format(name))
        return value

    def parse_binary_operation(self, node, left, operator, right, state):
        operation = state.BinaryOperation(
            left = left,
            operator = operator,
            right = right,
            )
        if isinstance(operator, (ast.Add, ast.Div, ast.FloorDiv, ast.Mult, ast.Sub)):
            if isinstance(left, state.Array) and isinstance(right, state.Array):
                if left.data_type == np.bool and right.data_type == np.bool:
                    data_type = np.bool
                elif left.data_type in (np.bool, np.int16, np.int32) \
                        and right.data_type in (np.bool, np.int16, np.int32):
                    data_type = np.int32
                elif left.data_type in (np.bool, np.float32, np.int16, np.int32) \
                        and right.data_type in (np.bool, np.float32, np.int16, np.int32):
                    data_type = np.float32
                else:
                    assert False, '{} {} {}'.format(left.data_type, operator, right.data_type)
                assert left.entity_key_plural == right.entity_key_plural
                value = state.Array(
                    data_type = data_type,
                    entity_key_plural = left.entity_key_plural,
                    operation = operation,
                    )
                return value, None
            if isinstance(left, state.Array) and isinstance(right, state.DateTime64):
                value = state.Array(
                    data_type = np.datetime64,
                    entity_key_plural = left.entity_key_plural,
                    operation = operation,
                    )
                return value, None
            if isinstance(left, state.Array) and isinstance(right, (state.LawNode, state.Number)):
                if left.data_type == np.bool and right.data_type == bool:
                    data_type = np.bool
                elif left.data_type in (np.bool, np.int16, np.int32) and right.data_type in (bool, int):
                    data_type = np.int32
                elif left.data_type in (np.bool, np.float32, np.int16, np.int32) \
                        and right.data_type in (bool, float, int):
                    data_type = np.float32
                else:
                    assert False, '{} {} {}'.format(left.data_type, operator, right.data_type)
                value = state.Array(
                    data_type = data_type,
                    entity_key_plural = left.entity_key_plural,
                    operation = operation,
                    )
                return value, None
            if isinstance(left, state.DateTime64) and isinstance(right, state.Array):
                value = state.Array(
                    data_type = np.datetime64,
                    entity_key_plural = right.entity_key_plural,
                    operation = operation,
                    )
                return value, None
            if isinstance(left, (state.LawNode, state.Number)) and isinstance(right, state.Array):
                if left.data_type == bool and right.data_type == np.bool:
                    data_type = np.bool
                elif left.data_type in (bool, int) and right.data_type in (np.bool, np.int16, np.int32):
                    data_type = np.int32
                elif left.data_type in (bool, float, int) \
                        and right.data_type in (np.bool, np.float32, np.int16, np.int32):
                    data_type = np.float32
                else:
                    assert False, '{} {} {}'.format(left.data_type, operator, right.data_type)
                value = state.Array(
                    data_type = data_type,
                    entity_key_plural = right.entity_key_plural,
                    operation = operation,
                    )
                return value, None
            if isinstance(left, (state.LawNode, state.Number)) and isinstance(right, (state.LawNode, state.Number)):
                if left.data_type == bool and right.data_type == bool:
                    data_type = bool
                elif left.data_type in (bool, int) and right.data_type in (bool, int):
                    data_type = int
                elif left.data_type in (bool, float, int) and right.data_type in (bool, float, int):
                    data_type = float
                else:
                    assert False, '{} {} {}'.format(left.data_type, operator, right.data_type)
                value = state.Number(
                    data_type = data_type,
                    operation = operation,
                    )
                return value, None
            assert False, 'left: {}\n    operator: {}\n    right: {}\n    node: {}'.format(left, operator, right,
                ast.dump(node))
        if isinstance(operator, (ast.BitAnd, ast.BitOr)):
            if isinstance(left, state.Array) and isinstance(right, state.Array):
                if left.data_type == np.bool and right.data_type in (np.bool, np.int16, np.int32):
                    data_type = np.bool
                elif left.data_type in (np.bool, np.int16, np.int32) and right.data_type == np.bool:
                    data_type = np.bool
                else:
                    assert False, '{} {} {}'.format(left.data_type, operator, right.data_type)
                assert left.entity_key_plural == right.entity_key_plural
                value = state.Array(
                    data_type = data_type,
                    entity_key_plural = left.entity_key_plural,
                    operation = operation,
                    )
                return value, None
            if isinstance(left, state.Number) and isinstance(right, state.Number):
                if left.data_type == bool and right.data_type == bool:
                    data_type = bool
                else:
                    assert False, '{} {} {}'.format(left.data_type, operator, right.data_type)
                value = state.Number(
                    data_type = data_type,
                    operation = operation,
                    )
                return value, None
            assert False, 'left: {}\n    operator: {}\n    right: {}\n    node: {}'.format(left, operator, right,
                ast.dump(node))
        if isinstance(operator, ast.Mult):
            if isinstance(left, state.Array) and isinstance(right, state.Array):
                if left.data_type == np.float32 and right.data_type == np.float32:
                    data_type = np.float32
                else:
                    assert False, '{} {} {}'.format(left.data_type, operator, right.data_type)
                assert left.entity_key_plural == right.entity_key_plural
                value = state.Array(
                    data_type = data_type,
                    entity_key_plural = left.entity_key_plural,
                    operation = operation,
                    )
                return value, None
            if isinstance(left, state.Array) and isinstance(right, (state.LawNode, state.Number)):
                if left.data_type in (np.float32, np.int16, np.int32) and right.data_type == float:
                    data_type = np.float32
                else:
                    assert False, '{} {} {}'.format(left.data_type, operator, right.data_type)
                value = state.Array(
                    data_type = data_type,
                    entity_key_plural = left.entity_key_plural,
                    operation = operation,
                    )
                return value, None
            if isinstance(left, (state.LawNode, state.Number)) and isinstance(right, state.Array):
                if left.data_type == float and right.data_type in (np.float32, np.int16, np.int32):
                    data_type = np.float32
                else:
                    assert False, '{} {} {}'.format(left.data_type, operator, right.data_type)
                value = state.Array(
                    data_type = data_type,
                    entity_key_plural = right.entity_key_plural,
                    operation = operation,
                    )
                return value, None
            assert False, 'left: {}\n    operator: {}\n    right: {}\n    node: {}'.format(left, operator, right,
                ast.dump(node))
        assert False, 'left: {}\n    operator: {}\n    right: {}\n    node: {}'.format(left, operator, right,
            ast.dump(node))

    def parse_call(self, node, state):
        assert isinstance(node, ast.Call), ast.dump(node)
        function = node.func
        positional_arguments = conv.check(conv.uniform_sequence(self.parse_value))(node.args, state)
        named_arguments = collections.OrderedDict(
            (keyword.arg, conv.check(self.parse_value)(keyword.value, state))
            for keyword in node.keywords
            )
        star_arguments = conv.check(self.parse_value)(node.starargs, state) if node.starargs is not None else None
        if star_arguments is not None:
            assert isinstance(star_arguments, (list, tuple)), star_arguments
            # print 'positional_arguments =', positional_arguments
            # print 'star_arguments =', star_arguments
            positional_arguments.extend(star_arguments)
            # print 'positional_arguments =', positional_arguments
            # print ast.dump(node)
        keyword_arguments = conv.check(self.parse_value)(node.kwargs, state) if node.kwargs is not None else None
        assert keyword_arguments is None, ast.dump(node)
        if isinstance(function, ast.Attribute):
            assert isinstance(function.ctx, ast.Load), ast.dump(node)
            value = conv.check(self.parse_value)(function.value, state)
            if isinstance(value, state.Array):
                method_name = function.attr
                if method_name in ('all', 'any'):
                    assert value.data_type == np.bool, ast.dump(node)
                    assert len(positional_arguments) == 0, ast.dump(node)
                    assert len(named_arguments) == 0, ast.dump(node)
                    test = state.Number(
                        data_type = bool,
                        operation = value,
                        )
                    return test, None
                if method_name == 'astype':
                    assert len(positional_arguments) == 1, ast.dump(node)
                    assert len(named_arguments) == 0, ast.dump(node)
                    new_type = positional_arguments[0]
                    if isinstance(new_type, state.String):
                        if new_type.value in ('timedelta64[Y]', 'timedelta64[M]'):
                            assert value.data_type == np.datetime64
                            test = state.Array(
                                data_type = np.int32,
                                entity_key_plural = value.entity_key_plural,
                                operation = value,
                                )
                            return test, None
                        assert False, 'Unhandled data type {} for array method {}({}) in node {}'.format(
                            value.data_type, method_name, new_type, ast.dump(node))
                    if isinstance(new_type, state.Type):
                        if new_type.value is np.int16:
                            assert value.data_type == np.bool
                            test = state.Array(
                                data_type = np.int16,
                                entity_key_plural = value.entity_key_plural,
                                operation = value,
                                )
                            return test, None
                        assert False, 'Unhandled data type {} for array method {}({}) in node {}'.format(
                            value.data_type, method_name, new_type, ast.dump(node))
                    assert False, 'Unhandled data type {} for array method {}({}) in node {}'.format(value.data_type,
                        method_name, new_type, ast.dump(node))
                assert False, 'Unknown array method {} in node {}'.format(method_name, ast.dump(node))
            if isinstance(value, state.Formula):
                method_name = function.attr
                if method_name == 'any_by_roles':
                    assert len(positional_arguments) == 1, ast.dump(node)
                    array_or_dated_holder = positional_arguments[0]
                    assert isinstance(array_or_dated_holder, (state.Array, state.DatedHolder))
                    default = named_arguments.get('default')
                    assert default is None, ast.dump(node)
                    entity = named_arguments.get('entity')
                    assert entity is None, ast.dump(node)
                    roles = named_arguments.get('roles')
                    if roles is not None:
                        assert isinstance(roles, list), ast.dump(node)
                        assert all(
                            isinstance(role, state.Number) and isinstance(role.value, int)
                            for role in roles
                            ), ast.dump(node)
                    # operation = state.EntityToEntity(method_name = method_name,
                    #     named_arguments = named_arguments, positional_arguments = positional_arguments)
                    array = state.Array(
                        data_type = np.bool,
                        entity_key_plural = state.column.entity_key_plural,
                        # operation = operation,
                        )
                    return array, None
                if method_name == 'cast_from_entity_to_role':
                    assert len(positional_arguments) == 1, ast.dump(node)
                    array_or_dated_holder = positional_arguments[0]
                    assert isinstance(array_or_dated_holder, (state.Array, state.DatedHolder))
                    default = named_arguments.get('default')
                    assert default is None, ast.dump(node)
                    entity = named_arguments.get('entity')
                    assert entity is None, ast.dump(node)
                    role = named_arguments['role']
                    assert isinstance(role, state.Number), ast.dump(node)
                    assert isinstance(role.value, int), ast.dump(node)
                    # operation = state.EntityToEntity(method_name = method_name,
                    #     named_arguments = named_arguments, positional_arguments = positional_arguments)
                    array = state.Array(
                        data_type = array_or_dated_holder.data_type,
                        entity_key_plural = u'individus',  # TODO
                        # operation = operation,
                        )
                    return array, None
                if method_name == 'cast_from_entity_to_roles':
                    assert len(positional_arguments) == 1, ast.dump(node)
                    array_or_dated_holder = positional_arguments[0]
                    assert isinstance(array_or_dated_holder, (state.Array, state.DatedHolder))
                    default = named_arguments.get('default')
                    assert default is None, ast.dump(node)
                    entity = named_arguments.get('entity')
                    assert entity is None, ast.dump(node)
                    roles = named_arguments.get('roles')
                    if roles is not None:
                        assert isinstance(roles, list), ast.dump(node)
                        assert all(
                            isinstance(role, state.Number) and isinstance(role.value, int)
                            for role in roles
                            ), ast.dump(node)
                    # operation = state.EntityToEntity(method_name = method_name,
                    #     named_arguments = named_arguments, positional_arguments = positional_arguments)
                    array = state.Array(
                        data_type = array_or_dated_holder.data_type,
                        entity_key_plural = u'individus',  # TODO
                        # operation = operation,
                        )
                    return array, None
                if method_name == 'filter_role':
                    assert len(positional_arguments) == 1, ast.dump(node)
                    array_or_dated_holder = positional_arguments[0]
                    assert isinstance(array_or_dated_holder, (state.Array, state.DatedHolder))
                    default = named_arguments.get('default')
                    assert default is None, ast.dump(node)
                    entity = named_arguments.get('entity')
                    assert entity is None, ast.dump(node)
                    role = named_arguments['role']
                    assert isinstance(role, state.Number), ast.dump(node)
                    assert isinstance(role.value, int), ast.dump(node)
                    # operation = state.EntityToEntity(method_name = method_name,
                    #     named_arguments = named_arguments, positional_arguments = positional_arguments)
                    array = state.Array(
                        data_type = array_or_dated_holder.data_type,
                        entity_key_plural = state.column.entity_key_plural,
                        # operation = operation,
                        )
                    return array, None
                if method_name == 'split_by_roles':
                    assert len(positional_arguments) == 1, ast.dump(node)
                    array_or_dated_holder = positional_arguments[0]
                    assert isinstance(array_or_dated_holder, (state.Array, state.DatedHolder))
                    default = named_arguments.get('default')
                    assert default is None, ast.dump(node)
                    entity = named_arguments.get('entity')
                    assert entity is None, ast.dump(node)
                    roles = named_arguments.get('roles')
                    if roles is not None:
                        if isinstance(roles, list):
                            assert all(
                                isinstance(role, state.Number) and isinstance(role.value, int)
                                for role in roles
                                ), ast.dump(node)
                        elif isinstance(roles, state.UniformList) and isinstance(roles.item, state.Number) \
                                and roles.item.data_type == int:
                            pass
                        else:
                            assert False, ast.dump(node)
                    # operation = state.EntityToEntity(method_name = method_name,
                    #     named_arguments = named_arguments, positional_arguments = positional_arguments)
                    array_by_role = state.UniformDictionary(
                        key = state.Number(),
                        value = state.Array(
                            data_type = array_or_dated_holder.data_type,
                            entity_key_plural = state.column.entity_key_plural,
                            # operation = operation,
                            ),
                        )
                    return array_by_role, None
                if method_name == 'sum_by_entity':
                    assert len(positional_arguments) == 1, ast.dump(node)
                    array_or_dated_holder = positional_arguments[0]
                    assert isinstance(array_or_dated_holder, (state.Array, state.DatedHolder))
                    default = named_arguments.get('default')
                    assert default is None, ast.dump(node)
                    entity = named_arguments.get('entity')
                    assert entity is None, ast.dump(node)
                    roles = named_arguments.get('roles')
                    if roles is not None:
                        assert isinstance(roles, list), ast.dump(node)
                        assert all(
                            isinstance(role, state.Number) and isinstance(role.value, int)
                            for role in roles
                            ), ast.dump(node)
                    # operation = state.EntityToEntity(method_name = method_name,
                    #     named_arguments = named_arguments, positional_arguments = positional_arguments)
                    array = state.Array(
                        data_type = (array_or_dated_holder.data_type
                            if array_or_dated_holder.data_type != np.bool
                            else np.int32),
                        entity_key_plural = state.column.entity_key_plural,
                        # operation = operation,
                        )
                    return array, None
                assert False, ast.dump(node)
            if isinstance(value, state.LawNode):
                method_name = function.attr
                if method_name == 'add_bracket':
                    # assert len(positional_arguments) == 1, ast.dump(node)
                    # assert len(named_arguments) == 0, ast.dump(node)
                    # tax_scale = positional_arguments[0]
                    # assert isinstance(tax_scale, (state.LawNode, state.TaxScalesTree)), ast.dump(node)
                    return state.LawNode(), None
                if method_name == 'add_tax_scale':
                    assert len(positional_arguments) == 1, ast.dump(node)
                    assert len(named_arguments) == 0, ast.dump(node)
                    tax_scale = positional_arguments[0]
                    assert isinstance(tax_scale, (state.LawNode, state.TaxScalesTree)), ast.dump(node)
                    return state.LawNode(), None
                if method_name == 'calc':
                    assert len(positional_arguments) == 1, ast.dump(node)
                    assert len(named_arguments) == 0, ast.dump(node)
                    input_array = positional_arguments[0]
                    assert isinstance(input_array, state.Array), ast.dump(node)
                    array = state.Array(
                        data_type = input_array.data_type,
                        entity_key_plural = input_array.entity_key_plural,
                        # operation = operation,
                        )
                    return array, None
                if method_name == 'inverse':
                    assert len(positional_arguments) == 0, ast.dump(node)
                    assert len(named_arguments) == 0, ast.dump(node)
                    return state.LawNode(), None
                assert False, 'Unknown LawNode method {} in node {}'.format(method_name, ast.dump(node))
            if isinstance(value, state.Logger):
                # Ignore logging methods.
                return None, None
            if isinstance(value, state.Math):
                method_name = function.attr
                if method_name == 'floor':
                    return state.Number(data_type = float), None
                assert False, 'Unknown math method {} in node {}'.format(method_name, ast.dump(node))
            if isinstance(value, state.TaxScalesTree):
                method_name = function.attr
                if method_name == 'add_bracket':
                    # assert len(positional_arguments) == 1, ast.dump(node)
                    # assert len(named_arguments) == 0, ast.dump(node)
                    # tax_scale = positional_arguments[0]
                    # assert isinstance(tax_scale, (state.LawNode, state.TaxScalesTree)), ast.dump(node)
                    return state.LawNode(), None
                if method_name == 'add_tax_scale':
                    assert len(positional_arguments) == 1, ast.dump(node)
                    assert len(named_arguments) == 0, ast.dump(node)
                    tax_scale = positional_arguments[0]
                    assert isinstance(tax_scale, (state.LawNode, state.TaxScalesTree)), ast.dump(node)
                    return state.LawNode(), None
                if method_name == 'calc':
                    assert len(positional_arguments) == 1, ast.dump(node)
                    assert len(named_arguments) == 0, ast.dump(node)
                    input_array = positional_arguments[0]
                    assert isinstance(input_array, state.Array), ast.dump(node)
                    array = state.Array(
                        data_type = input_array.data_type,
                        entity_key_plural = input_array.entity_key_plural,
                        # operation = operation,
                        )
                    return array, None
                if method_name == 'get':
                    assert len(positional_arguments) == 1, ast.dump(node)
                    assert len(named_arguments) == 0, ast.dump(node)
                    name = positional_arguments[0]
                    assert isinstance(name, state.String), ast.dump(node)
                    return state.TaxScalesTree(), None
                if method_name == 'inverse':
                    assert len(positional_arguments) == 0, ast.dump(node)
                    assert len(named_arguments) == 0, ast.dump(node)
                    return state.LawNode(), None
                if method_name == 'itervalues':
                    assert len(positional_arguments) == 0, ast.dump(node)
                    assert len(named_arguments) == 0, ast.dump(node)
                    return state.UniformIterator(item = state.TaxScalesTree()), None
                if method_name == 'keys':
                    assert len(positional_arguments) == 0, ast.dump(node)
                    assert len(named_arguments) == 0, ast.dump(node)
                    return state.UniformList(item = state.String()), None
                if method_name == 'multiply_rates':
                    # assert len(positional_arguments) == 1, ast.dump(node)
                    # assert len(named_arguments) == 0, ast.dump(node)
                    # tree = positional_arguments[0]
                    # assert isinstance(tree, state.TaxScalesTree), ast.dump(node)
                    return state.LawNode(), None
                if method_name == 'update':
                    assert len(positional_arguments) == 1, ast.dump(node)
                    assert len(named_arguments) == 0, ast.dump(node)
                    tree = positional_arguments[0]
                    assert isinstance(tree, state.TaxScalesTree), ast.dump(node)
                    return state.TaxScalesTree(), None
                assert False, 'Unknown TaxScalesTree method {} in node {}'.format(method_name, ast.dump(node))
            if isinstance(value, state.UniformDictionary):
                method_name = function.attr
                if method_name == 'iterkeys':
                    assert len(positional_arguments) == 0, ast.dump(node)
                    assert len(named_arguments) == 0, ast.dump(node)
                    return state.UniformIterator(item = value.key), None
                if method_name == 'iteritems':
                    assert len(positional_arguments) == 0, ast.dump(node)
                    assert len(named_arguments) == 0, ast.dump(node)
                    return state.UniformIterator(item = state.Structure([value.key, value.value])), None
                if method_name == 'itervalues':
                    assert len(positional_arguments) == 0, ast.dump(node)
                    assert len(named_arguments) == 0, ast.dump(node)
                    return state.UniformIterator(item = value.value), None
                assert False, 'Unknown UniformDictionary method {} in node {}'.format(method_name, ast.dump(node))
            assert False, 'Unhandled container {} in node {}'.format(value, ast.dump(node))
        assert isinstance(function, ast.Name), ast.dump(node)
        assert isinstance(function.ctx, ast.Load), ast.dump(node)
        function_name = function.id
        if function_name in ('around', 'round'):
            assert 1 <= len(positional_arguments) <= 2, ast.dump(node)
            assert len(named_arguments) == 0, ast.dump(node)
            array = positional_arguments[0]
            assert isinstance(array, (state.Array, state.LawNode, state.Number)), ast.dump(node)
            if len(positional_arguments) >= 2:
                decimals = positional_arguments[1]
                assert isinstance(decimals, state.Number), ast.dump(node)
            return array, None
        if function_name == 'combine_tax_scales':
            assert 1 <= len(positional_arguments) <= 2, ast.dump(node)
            assert len(named_arguments) == 0, ast.dump(node)
            tax_scales_tree = positional_arguments[0]
            assert isinstance(tax_scales_tree, state.TaxScalesTree), ast.dump(node)
            return state.LawNode(), None
        if function_name == 'datetime64':
            assert len(positional_arguments) == 1, ast.dump(node)
            assert len(named_arguments) == 0, ast.dump(node)
            date = positional_arguments[0]
            assert isinstance(date, state.Date), ast.dump(node)
            return state.DateTime64(), None
        if function_name in ('ceil', 'floor', 'not_'):
            assert len(positional_arguments) == 1, ast.dump(node)
            assert len(named_arguments) == 0, ast.dump(node)
            array = positional_arguments[0]
            assert isinstance(array, (state.Array, state.LawNode, state.Number)), ast.dump(node)
            return array, None
        if function_name == 'fsolve':
            assert len(positional_arguments) == 2, ast.dump(node)
            assert len(named_arguments) == 0, ast.dump(node)
            function = positional_arguments[0]
            assert isinstance(function, state.FunctionDefinition), ast.dump(node)
            array = positional_arguments[1]
            assert isinstance(array, state.Array), ast.dump(node)
            result = state.Array(
                column = state.column,
                data_type = state.column.dtype,
                entity_key_plural = state.column.entity_key_plural,
                # operation = operation,
                )
            return result, None
        if function_name == 'hasattr':
            assert 2 <= len(positional_arguments) <= 3, ast.dump(node)
            assert len(named_arguments) == 0, ast.dump(node)
            return state.Number(data_type = bool), None
        if function_name == 'izip':
            assert len(positional_arguments) >= 2, ast.dump(node)
            assert len(named_arguments) == 0, ast.dump(node)
            items = []
            for iterable in positional_arguments:
                if isinstance(iterable, (state.UniformIterator, state.UniformList)):
                    items.append(iterable.item)
                else:
                    assert False, 'Unhandled iterable {} in izip for node {}'.format(iterable, ast.dump(node))
            return state.UniformIterator(item = state.Structure(items)), None
        if function_name == 'len':
            assert len(positional_arguments) == 1, ast.dump(node)
            assert len(named_arguments) == 0, ast.dump(node)
            value = positional_arguments[0]
            assert isinstance(value, state.Array), ast.dump(node)
            return state.ArrayLength(array = value), None
        if function_name == 'MarginalRateTaxScale':
            # assert len(positional_arguments) == 2, ast.dump(node)
            # assert len(named_arguments) == 0, ast.dump(node)
            # name_argument = positional_arguments[0]
            # assert isinstance(name_argument, state.String), ast.dump(node)
            # law_node = positional_arguments[1]
            # assert isinstance(law_node, state.LawNode), ast.dump(node)
            return state.LawNode(), None
        if function_name in ('max_', 'min_'):
            assert len(positional_arguments) == 2, ast.dump(node)
            assert len(named_arguments) == 0, ast.dump(node)
            result = positional_arguments[0]
            assert isinstance(result, (state.Array, state.LawNode, state.Number)), ast.dump(node)
            for argument in positional_arguments[1:]:
                if isinstance(result, state.Array) and isinstance(argument, state.Array):
                    if result.data_type == np.bool and argument.data_type == np.bool:
                        data_type = np.bool
                    elif result.data_type in (np.bool, np.int16, np.int32) \
                            and argument.data_type in (np.bool, np.int16, np.int32):
                        data_type = np.int32
                    elif result.data_type in (np.bool, np.float32, np.int16, np.int32) \
                            and argument.data_type in (np.bool, np.float32, np.int16, np.int32):
                        data_type = np.float32
                    else:
                        assert False, '{}({}, {})'.format(function_name, result.data_type, argument.data_type)
                    assert result.entity_key_plural == argument.entity_key_plural
                    result = state.Array(
                        data_type = data_type,
                        entity_key_plural = result.entity_key_plural,
                        # operation = operation,
                        )
                elif isinstance(result, state.Array) and isinstance(argument, (state.LawNode, state.Number)):
                    if result.data_type == np.bool and argument.data_type == bool:
                        data_type = np.bool
                    elif result.data_type in (np.bool, np.int16, np.int32) and argument.data_type in (bool, int):
                        data_type = np.int32
                    elif result.data_type in (np.bool, np.float32, np.int16, np.int32) \
                            and argument.data_type in (bool, float, int):
                        data_type = np.float32
                    else:
                        assert False, '{}({}, {})'.format(function_name, result.data_type, argument.data_type)
                    result = state.Array(
                        data_type = data_type,
                        entity_key_plural = result.entity_key_plural,
                        # operation = operation,
                        )
                elif isinstance(result, (state.LawNode, state.Number)) and isinstance(argument, state.Array):
                    if result.data_type == bool and argument.data_type == np.bool:
                        data_type = np.bool
                    elif result.data_type in (bool, int) and argument.data_type in (np.bool, np.int16, np.int32):
                        data_type = np.int32
                    elif result.data_type in (bool, float, int) \
                            and argument.data_type in (np.bool, np.float32, np.int16, np.int32):
                        data_type = np.float32
                    else:
                        assert False, '{}({}, {})'.format(function_name, result.data_type, argument.data_type)
                    result = state.Array(
                        data_type = data_type,
                        entity_key_plural = argument.entity_key_plural,
                        # operation = operation,
                        )
                else:
                    assert False, '{}({}, {})\n    node: {}'.format(function_name, result, argument, ast.dump(node))
            return result, None
        if function_name in ('and_', 'or_', 'xor_'):
            assert len(positional_arguments) == 2, ast.dump(node)
            assert len(named_arguments) == 0, ast.dump(node)
            result = positional_arguments[0]
            assert isinstance(result, (state.Array, state.LawNode, state.Number)), ast.dump(node)
            for argument in positional_arguments[1:]:
                if isinstance(result, state.Array) and isinstance(argument, state.Array):
                    assert result.entity_key_plural == argument.entity_key_plural
                    result = state.Array(
                        data_type = np.bool,
                        entity_key_plural = result.entity_key_plural,
                        # operation = operation,
                        )
                elif isinstance(result, state.Array) and isinstance(argument, (state.LawNode, state.Number)):
                    result = state.Array(
                        data_type = np.bool,
                        entity_key_plural = result.entity_key_plural,
                        # operation = operation,
                        )
                elif isinstance(result, (state.LawNode, state.Number)) and isinstance(argument, state.Array):
                    result = state.Array(
                        data_type = np.bool,
                        entity_key_plural = argument.entity_key_plural,
                        # operation = operation,
                        )
                else:
                    assert False, '{}({}, {})\n    node: {}'.format(function_name, result, argument, ast.dump(node))
            return result, None
        if function_name in ('ones', 'zeros'):
            assert len(positional_arguments) == 1, ast.dump(node)
            assert 0 <= len(named_arguments) <= 1, ast.dump(node)
            length = positional_arguments[0]
            assert isinstance(length, state.ArrayLength), ast.dump(node)
            cast_type = named_arguments.get('dtype')
            if cast_type is None:
                data_type = np.float32  # Should be np.float64
            else:
                assert isinstance(cast_type, state.Type), ast.dump(node)
                data_type = cast_type.value
            result = state.Array(
                data_type = data_type,
                entity_key_plural = length.array.entity_key_plural,
                # operation = operation,
                )
            return result, None
        if function_name == 'scale_tax_scales':
            assert len(positional_arguments) == 2, ast.dump(node)
            assert len(named_arguments) == 0, ast.dump(node)
            tax_scales_tree = positional_arguments[0]
            assert isinstance(tax_scales_tree, (state.LawNode, state.TaxScalesTree)), ast.dump(node)
            factor_argument = positional_arguments[1]
            assert isinstance(factor_argument, (state.LawNode, state.Number)), ast.dump(node)
            return tax_scales_tree.__class__(), None
        if function_name == 'startswith':
            assert len(positional_arguments) == 2, ast.dump(node)
            assert len(named_arguments) == 0, ast.dump(node)
            left = positional_arguments[0]
            right = positional_arguments[1]
            if isinstance(left, state.Array):
                value = state.Array(
                    data_type = np.bool,
                    entity_key_plural = left.entity_key_plural,
                    # operation = operation,
                    )
                return value, None
            assert False, '{}({}, {})\n    node: {}'.format(function_name, left, right, ast.dump(node))
        if function_name == 'TaxScalesTree':
            assert len(positional_arguments) == 2, ast.dump(node)
            assert len(named_arguments) == 0, ast.dump(node)
            name_argument = positional_arguments[0]
            assert isinstance(name_argument, state.String), ast.dump(node)
            law_node = positional_arguments[1]
            assert isinstance(law_node, state.LawNode), ast.dump(node)
            return state.TaxScalesTree(), None
        if function_name == 'where':
            assert 1 <= len(positional_arguments) <= 3, ast.dump(node)
            assert len(named_arguments) == 0, ast.dump(node)
            condition = positional_arguments[0]
            x = positional_arguments[1] if len(positional_arguments) >= 2 else None
            y = positional_arguments[2] if len(positional_arguments) >= 3 else None
            if isinstance(condition, state.Array):
                data_type = np.bool if x is None and y is None else x.data_type if x is not None else y.data_type
                if data_type is int:
                    data_type = np.int32
                value = state.Array(
                    data_type = data_type,
                    entity_key_plural = condition.entity_key_plural,
                    # operation = operation,
                    )
                return value, None
            assert False, '{}({}...)\n    node: {}'.format(function_name, condition, ast.dump(node))
        local_function = self.get_value_by_name(function_name, default = None, state = state)
        if local_function is not None and isinstance(local_function, state.FunctionDefinition):
            return local_function.call(named_arguments = named_arguments, positional_arguments = positional_arguments,
                state = state)
        assert False, ast.dump(node)

    def parse_statement(self, node, state):
        if isinstance(node, ast.Assert):
            # TODO
            return None, None
        if isinstance(node, ast.Assign):
            targets = node.targets
            assert len(targets) == 1, targets
            target = targets[0]
            assert isinstance(target.ctx, ast.Store), ast.dump(node)
            if isinstance(target, ast.Name):
                self.value_by_name[target.id] = conv.check(self.parse_value)(node.value, state)
                return None, None
            if isinstance(target, ast.Subscript):
                # For example: salarie['fonc']['etat']['excep_solidarite'] = salarie['fonc']['commun']['solidarite']
                return None, None
            if isinstance(target, ast.Tuple):
                assert isinstance(node.value, ast.Tuple), ast.dump(node)
                assert len(target.elts) == len(node.value.elts), ast.dump(node)
                for name_element, value in itertools.izip(target.elts, node.value.elts):
                    self.value_by_name[name_element.id] = conv.check(self.parse_value)(value, state)
                return None, None
            assert False, ast.dump(node)
        if isinstance(node, ast.AugAssign):
            target = node.target
            assert isinstance(target.ctx, ast.Store), ast.dump(node)
            if isinstance(target, ast.Name):
                left = self.get_value_by_name(target.id, state = state)
                right = conv.check(self.parse_value)(node.value, state)
                value, error = self.parse_binary_operation(node, left, node.op, right, state)
                if error is not None:
                    return value, error
                self.value_by_name[target.id] = value
                return None, None
            assert False, ast.dump(node)
        if isinstance(node, ast.Continue):
            return state.Continue(), None
        if isinstance(node, ast.Expr):
            conv.check(self.parse_value)(node.value, state)
            return None, None
        if isinstance(node, ast.For):
            target = node.target
            assert isinstance(target.ctx, ast.Store), ast.dump(node)
            if isinstance(target, ast.Name):
                iter = conv.check(self.parse_value)(node.iter, state)
                if isinstance(iter, state.Enum):
                    loop_item = state.Structure([
                        state.String(),
                        state.Number(
                            data_type = int,
                            ),
                        ])
                elif isinstance(iter, (state.UniformIterator, state.UniformList)):
                    loop_item = iter.item
                else:
                    assert False, 'Unhandled loop item {} in {}'.format(iter, ast.dump(node))
                self.value_by_name[target.id] = loop_item
            elif isinstance(target, ast.Tuple):
                targets = target
                iters = conv.check(self.parse_value)(node.iter, state)
                if isinstance(iters, state.UniformIterator):
                    iter = iters.item
                    if isinstance(iter, state.Structure):
                        for target, loop_item in itertools.izip(targets.elts, iter.items):
                            self.value_by_name[target.id] = loop_item
                    else:
                        assert False, "Unhandled loop item {} in node {}".format(iter, ast.dump(node))
                else:
                    assert False, "Unhandled loop items {} in node {}".format(iters, ast.dump(node))
            else:
                assert False, "Unexpected target {} in node {}".format(target, ast.dump(node))
            execute_body = True
            execute_orelse = True
            if execute_body:
                for statement in node.body:
                    statement = conv.check(self.parse_statement)(statement, state)
                    if isinstance(statement, (state.Continue, state.Return)):
                        if execute_orelse:
                            # Value of test is unknown. Stop execution of body but don't return result.
                            break
                        return statement, None
            if execute_orelse:
                for statement in node.orelse:
                    statement = conv.check(self.parse_statement)(statement, state)
                    if isinstance(statement, (state.Continue, state.Return)):
                        if execute_body:
                            # Value of test is unknown. Stop execution of body but don't return result.
                            break
                        return statement, None
            return None, None
        if isinstance(node, ast.FunctionDef):
            function_definition = state.FunctionDefinition(container = self, module = self.definition.module,
                node = node, state = state)
            self.value_by_name[node.name] = function_definition
            return function_definition, None
        if isinstance(node, ast.Global):
            for name in node.names:
                # TODO: Currently handle globals as local variables.
                self.value_by_name[name] = None
            return None, None
        if isinstance(node, ast.If):
            test = conv.check(self.parse_value)(node.test, state)
            if isinstance(test, state.Number) and test.value is not UnboundLocalError:
                execute_body = bool(test.value)
                execute_orelse = not execute_body
            else:
                execute_body = True
                execute_orelse = True
            return_statement = None
            if execute_body:
                for statement in node.body:
                    statement = conv.check(self.parse_statement)(statement, state)
                    if isinstance(statement, state.Continue):
                        if execute_orelse:
                            # Value of test is unknown. Stop execution of body but don't return result.
                            break
                        return statement, None
                    if isinstance(statement, state.Return):
                        if execute_orelse:
                            # Value of test is unknown. Stop execution of body but don't return result.
                            return_statement = statement
                            break
                        return statement, None
            if execute_orelse:
                for statement in node.orelse:
                    statement = conv.check(self.parse_statement)(statement, state)
                    if isinstance(statement, state.Continue):
                        if execute_body:
                            # Value of test is unknown. Stop execution of body but don't return result.
                            break
                        return statement, None
                    if isinstance(statement, state.Return):
                        if execute_body:
                            # Value of test is unknown. Stop execution of body but don't return result.
                            return_statement = statement
                            break
                        return statement, None
            return return_statement, None
        if isinstance(node, ast.Pass):
            return None, None
        if isinstance(node, ast.Return):
            value = conv.check(self.parse_value)(node.value, state)
            result = state.Return(operation = value)
            return result, None
        return node, u'Unexpected AST node for statement'

    def parse_value(self, node, state):
        if isinstance(node, ast.Attribute):
            assert isinstance(node.ctx, ast.Load), ast.dump(node)
            container = conv.check(self.parse_value)(node.value, state)
            name = node.attr
            if isinstance(container, state.Entity):
                assert name == 'simulation', name
                simulation = state.Simulation()
                return simulation, None
            if isinstance(container, state.Formula):
                assert name == 'holder', name
                holder = state.Holder(formula = container)
                return holder, None
            if isinstance(container, state.Holder):
                assert name == 'entity', name
                entity = state.Entity()
                return entity, None
            if isinstance(container, state.Instant):
                if name == 'date':
                    return state.Date(), None
                assert name == 'year', name
                number = state.Number(data_type = int)  # TODO
                return number, None
            if isinstance(container, state.LawNode):
                if name == '__dict__':
                    return state.TaxScalesTree(), None
                law_node = state.LawNode(is_reference = container.is_reference, name = name, parent = container)
                return law_node, None
            if isinstance(container, state.Period):
                if name == 'date':
                    return state.Date(), None
                if name == 'start':
                    return state.Instant(), None
                assert False, 'Unhandled attribute {} for {} in {}'.format(name, container, ast.dump(node))
                instant = state.Instant()
                return instant, None
            if isinstance(container, state.TaxScalesTree):
                if name in ('name', 'option'):
                    return state.String(), None
                if name in 'rates':
                    return state.UniformList(item = state.Number(data_type = float)), None
                assert False, 'Unhandled attribute {} for {} in {}'.format(name, container, ast.dump(node))
            assert False, 'Unhandled attribute {} for {} in {}'.format(name, container, ast.dump(node))
        if isinstance(node, ast.BinOp):
            left = conv.check(self.parse_value)(node.left, state)
            right = conv.check(self.parse_value)(node.right, state)
            return self.parse_binary_operation(node, left, node.op, right, state)
        if isinstance(node, ast.Call):
            return self.parse_call(node, state)
        if isinstance(node, ast.Compare):
            left = conv.check(self.parse_value)(node.left, state)
            operators = node.ops
            comparators = conv.check(conv.uniform_sequence(self.parse_value))(node.comparators, state)
            test = left
            for operator, comparator in itertools.izip(operators, comparators):
                if isinstance(operator, (ast.Eq, ast.Gt, ast.GtE, ast.Lt, ast.LtE, ast.NotEq)):
                    if isinstance(test, state.Array) and isinstance(comparator, state.Array):
                        assert test.entity_key_plural == comparator.entity_key_plural
                        value = state.Array(
                            data_type = np.bool,
                            entity_key_plural = test.entity_key_plural,
                            # operation = operation,
                            )
                        return value, None
                    if isinstance(test, state.Array) and isinstance(comparator, (state.LawNode, state.Number)):
                        value = state.Array(
                            data_type = np.bool,
                            entity_key_plural = test.entity_key_plural,
                            # operation = operation,
                            )
                        return value, None
                    if isinstance(test, (state.LawNode, state.Number)) and isinstance(comparator, state.Array):
                        value = state.Array(
                            data_type = np.bool,
                            entity_key_plural = comparator.entity_key_plural,
                            # operation = operation,
                            )
                        return value, None
                    if isinstance(test, (state.LawNode, state.Number, state.String)) and isinstance(comparator,
                            (state.LawNode, state.Number, state.String)):
                        value = state.Number(
                            data_type = bool,
                            # operation = operation,
                            )
                        return value, None
                    assert False, 'left: {}\n    operator: {}\n    comparator: {}\n    node: {}'.format(test, operator,
                        comparator, ast.dump(node))
                if isinstance(operator, (ast.In, ast.NotIn)):
                    if isinstance(comparator, list):
                        value = state.Number(
                            data_type = bool,
                            # operation = operation,
                            )
                        return value, None
                    if isinstance(test, state.String) and isinstance(comparator, state.TaxScalesTree):
                        value = state.Number(
                            data_type = bool,
                            # operation = operation,
                            )
                        return value, None
                    # if isinstance(comparator, state.UniformDictionary):
                    #     if type(test) == type(comparator.key):
                    #         value = state.Number(
                    #             data_type = bool,
                    #             # operation = operation,
                    #             )
                    #         return value, None
                    #     assert False, 'left: {}\n    operator: {}\n    comparator: {}\n    node: {}'.format(test,
                    #         operator, comparator, ast.dump(node))
                    if isinstance(comparator, state.UniformList):
                        if type(test) == type(comparator.item):
                            value = state.Number(
                                data_type = bool,
                                # operation = operation,
                                )
                            return value, None
                        assert False, 'left: {}\n    operator: {}\n    comparator: {}\n    node: {}'.format(test,
                            operator, comparator, ast.dump(node))
                    assert False, 'left: {}\n    operator: {}\n    comparator: {}\n    node: {}'.format(test, operator,
                        comparator, ast.dump(node))
                if isinstance(operator, ast.Is):
                    value = state.Number(
                        data_type = bool,
                        # operation = operation,
                        )
                    return value, None
                assert False, 'left: {}\n    operator: {}\n    comparator: {}\n    node: {}'.format(test, operator,
                    comparator, ast.dump(node))
            return test, None
        if isinstance(node, ast.Lambda):
            return state.Lambda(container = self, module = self.definition.module, node = node, state = state), None
        if isinstance(node, ast.List):
            return [
                conv.check(self.parse_value)(element, state)
                for element in node.elts
                ], None
            return state.Number(data_type = type(node.n), value = node.n), None
        if isinstance(node, ast.Name):
            assert isinstance(node.ctx, ast.Load), ast.dump(node)
            if node.id == 'False':
                return state.Number(data_type = bool, value = False), None
            if node.id == 'math':
                return state.Math(), None
            if node.id == 'None':
                return None, None
            if node.id == 'True':
                return state.Number(data_type = bool, value = True), None
            return self.get_value_by_name(node.id, state = state), None
        if isinstance(node, ast.Num):
            return state.Number(data_type = type(node.n), value = node.n), None
        if isinstance(node, ast.Str):
            return state.String(value = node.s), None
        if isinstance(node, ast.Subscript):
            collection = conv.check(self.parse_value)(node.value, state)
            if isinstance(collection, state.Enum):
                assert isinstance(node.slice, ast.Index), ast.dump(node)
                index = conv.check(self.parse_value)(node.slice.value, state)
                assert isinstance(index, state.String), ast.dump(node)
                item = state.Number(
                    data_type = int,
                    )
                return item, None
            if isinstance(collection, state.LawNode):
                # For example: xxx.rate[i].
                assert isinstance(node.slice, ast.Index), ast.dump(node)
                index = conv.check(self.parse_value)(node.slice.value, state)
                if isinstance(index, (state.LawNode, state.Number)):
                    item = state.Number(
                        data_type = float,
                        # operation = TODO,
                        )
                    return item, None
                if isinstance(index, state.String):
                    return state.LawNode(), None
                assert False, ast.dump(node)
            if isinstance(collection, state.Structure):
                assert isinstance(node.slice, ast.Index), ast.dump(node)
                index = conv.check(self.parse_value)(node.slice.value, state)
                assert isinstance(index, (state.LawNode, state.Number, state.String)), ast.dump(node)
                assert index.value is not None, ast.dump(node)
                return collection.items[index.value], None
            if isinstance(collection, state.TaxScalesTree):
                assert isinstance(node.slice, ast.Index), ast.dump(node)
                index = conv.check(self.parse_value)(node.slice.value, state)
                assert isinstance(index, (state.LawNode, state.String)), ast.dump(node)
                return state.TaxScalesTree(), None
            if isinstance(collection, state.UniformDictionary):
                assert isinstance(node.slice, ast.Index), ast.dump(node)
                index = conv.check(self.parse_value)(node.slice.value, state)
                assert isinstance(index, collection.key.__class__), ast.dump(node)
                return collection.value, None
            if isinstance(collection, state.UniformList):
                assert isinstance(node.slice, ast.Index), ast.dump(node)
                index = conv.check(self.parse_value)(node.slice.value, state)
                assert isinstance(index, (state.LawNode, state.Number)), ast.dump(node)
                return collection.item, None
            assert False, 'Unhandled collection {} for subscript in {}'.format(collection, ast.dump(node))
        if isinstance(node, ast.Tuple):
            return tuple(
                conv.check(self.parse_value)(element, state)
                for element in node.elts
                ), None
        if isinstance(node, ast.UnaryOp):
            operand = conv.check(self.parse_value)(node.operand, state)
            operator = node.op
            operation = state.UnaryOperation(
                operand = operand,
                operator = operator,
                )
            if isinstance(operator, ast.Invert):
                if isinstance(operand, state.Array):
                    assert operand.data_type == np.bool, 'operator: {}\n    operand: {}\n    node: {}'.format(operator,
                        operand, ast.dump(node))
                    value = state.Array(
                        data_type = operand.data_type,
                        entity_key_plural = operand.entity_key_plural,
                        operation = operation,
                        )
                    return value, None
                assert False, 'operator: {}\n    operand: {}\n    node: {}'.format(operator, operand, ast.dump(node))
            if isinstance(operator, ast.Not):
                if isinstance(operand, list):
                    value = state.Number(
                        data_type = bool,
                        # operation = operation,
                        value = bool(operand),
                        )
                    return value, None
                assert False, 'operator: {}\n    operand: {}\n    node: {}'.format(operator, operand, ast.dump(node))
            if isinstance(operator, ast.USub):
                if isinstance(operand, state.Array):
                    assert operand.data_type in (np.float32, np.int16, np.int32), \
                        'operator: {}\n    operand: {}\n    node: {}'.format(operator, operand, ast.dump(node))
                    value = state.Array(
                        data_type = operand.data_type,
                        entity_key_plural = operand.entity_key_plural,
                        operation = operation,
                        )
                    return value, None
                if isinstance(operand, state.LawNode):
                    assert operand.data_type in (float, int), \
                        'operator: {}\n    operand: {}\n    node: {}'.format(operator, operand, ast.dump(node))
                    value = state.Number(
                        data_type = operand.data_type,
                        # operation = operation,
                        )
                    return value, None
                if isinstance(operand, state.Number):
                    assert operand.data_type in (float, int), \
                        'operator: {}\n    operand: {}\n    node: {}'.format(operator, operand, ast.dump(node))
                    value = state.Number(
                        data_type = operand.data_type,
                        # operation = operation,
                        value = -operand.value if operand.value is not None else None,
                        )
                    return value, None
                assert False, 'operator: {}\n    operand: {}\n    node: {}'.format(operator, operand, ast.dump(node))
            assert False, 'operator: {}\n    operand: {}\n    node: {}'.format(operator, operand, ast.dump(node))
        assert False, ast.dump(node)
        return None, None


class FunctionDefinition(object):
    container = None
    module = None
    node = None

    def __init__(self, container = None, module = None, node = None, state = None):
        assert container is not None
        self.container = container
        assert isinstance(module, state.Module)
        self.module = module
        assert node is not None
        self.node = node

    def call(self, named_arguments = None, positional_arguments = None, state = None):
        node = self.node
        function_call = state.FunctionCall(definition = self)
        assert not node.decorator_list, ast.dump(node)
        parameters = node.args
        for parameter, argument in itertools.izip(
                parameters.args[:len(parameters.args) - len(parameters.defaults)],
                positional_arguments,
                ):
            function_call.value_by_name[parameter.id] = argument
        if parameters.defaults:
            for parameter, default_argument in itertools.izip(
                    parameters.args[len(parameters.args) - len(parameters.defaults):],
                    parameters.defaults,
                    ):
                argument = named_arguments.get(parameter.id, UnboundLocalError)
                if argument is UnboundLocalError:
                    named_arguments[parameter.id] = conv.check(function_call.parse_value)(default_argument, state)
        if parameters.vararg is None:
            assert len(parameters.args) - len(parameters.defaults) == len(positional_arguments), ast.dump(node)  # TODO
        else:
            assert len(parameters.args) - len(parameters.defaults) <= len(positional_arguments), \
                str((ast.dump(node), positional_arguments))  # TODO # noqa
            function_call.value_by_name[parameters.vararg] = positional_arguments[len(parameters.args):]
        assert parameters.kwarg is None, ast.dump(node)  # TODO
        function_call.value_by_name.update(named_arguments)

        for statement in node.body:
            statement = conv.check(function_call.parse_statement)(statement, state)
            if isinstance(statement, state.Return):
                return statement.operation, None
        return None, None


class FunctionModule(object):
    # Caution: This is not the whole module, but only a dummy "module" containing only the formula.
    node = None

    def __init__(self, node, state):
        self.node = node

    def get_function_definition_class(self, state):
        return state.FunctionDefinition

    @classmethod
    def parse(cls, function, state):
        source_lines, line_number = inspect.getsourcelines(function)
        source = textwrap.dedent(''.join(source_lines))
        # print source
        node = ast.parse(source)
        if not isinstance(node, ast.Module):
            return node, u'Expected an AST node of class {}. Got: {}'.format(ast.Module, node)
        module = state.Module(python = inspect.getmodule(function), state = state)
        self = cls(node, state)
        for statement in node.body:
            # Assume that there is only one function definition.
            function_definition_class = self.get_function_definition_class(state)
            if not isinstance(statement, ast.FunctionDef):
                return statement, u'Expected an AST node of class {}. Got: {}'.format(ast.FunctionDef, node)
            return function_definition_class(container = module, module = module, node = statement, state = state), None
        assert False, 'Missing function definition in module: {}'.format(ast.dump(node))


class Holder(object):
    formula = None

    def __init__(self, formula = None):
        if formula is not None:
            self.formula = formula


class Instant(object):
    pass


class Lambda(FunctionDefinition):
    pass


class LawNode(object):
    data_type = float  # TODO
    is_reference = True
    name = None
    parent = None

    def __init__(self, is_reference = False, name = None, parent = None):
        if not is_reference:
            self.is_reference = False
        assert (parent is None) == (name is None), str((name, parent))
        if name is not None:
            self.name = name
        if parent is not None:
            assert isinstance(parent, LawNode)
            self.parent = parent

    def iter_names(self):
        parent = self.parent
        if parent is not None:
            for ancestor_name in parent.iter_names():
                yield ancestor_name
        name = self.name
        if name is not None:
            yield name

    @property
    def path(self):
        return '.'.join(self.iter_names())


class Logger(object):
    pass


class Math(object):
    pass


class Module(object):
    python = None
    value_by_name = None

    def __init__(self, python = None, state = None):
        if python is not None:
            # Python module
            self.python = python
        self.value_by_name = dict(
            CAT = state.Enum(),
            CHEF = state.Number(data_type = int, value = 0),
            CONJ = state.Number(data_type = int, value = 1),
            CREF = state.Number(data_type = int, value = 1),
            ENFS = state.UniformList(state.Number(data_type = int)),
            int16 = state.Type(np.int16),
            int32 = state.Type(np.int32),
            law = state.LawNode(),
            log = state.Logger(),
            PAC1 = state.Number(data_type = int, value = 2),
            PAC2 = state.Number(data_type = int, value = 3),
            PAC3 = state.Number(data_type = int, value = 4),
            PART = state.Number(data_type = int, value = 1),
            PREF = state.Number(data_type = int, value = 0),
            TAUX_DE_PRIME = state.Number(data_type = float, value = 1 / 4),
            VOUS = state.Number(data_type = int, value = 0),
            )

    def get_value_by_name(self, name, default = UnboundLocalError, state = None):
        value = self.value_by_name.get(name, UnboundLocalError)
        if value is UnboundLocalError:
            value = getattr(self.python, name, UnboundLocalError)
            if value is UnboundLocalError:
                if default is UnboundLocalError:
                    raise KeyError("Undefined value for {}".format(name))
                return default
            if not inspect.isfunction(value):
                # TODO?
                if default is UnboundLocalError:
                    raise KeyError("Undefined value for {}".format(name))
                return default
            function_definition = conv.check(state.FunctionModule.parse)(value, state)
            self.value_by_name[name] = value = function_definition
        return value


class Number(object):
    data_type = None
    operation = None
    value = UnboundLocalError

    def __init__(self, data_type = None, operation = None, value = UnboundLocalError):
        if data_type is not None:
            self.data_type = data_type
        if operation is not None:
            self.operation = operation
        if value is not UnboundLocalError:
            self.value = value


class Period(object):
    pass


class Return(object):
    operation = None

    def __init__(self, operation = None):
        if operation is not None:
            self.operation = operation


class Simulation(object):
    pass


class String(object):
    operation = None
    value = UnboundLocalError

    def __init__(self, operation = None, value = UnboundLocalError):
        if operation is not None:
            self.operation = operation
        if value is not UnboundLocalError:
            self.value = value


class Structure(object):
    items = None

    def __init__(self, items):
        self.items = items


class TaxScalesTree(object):
    pass


class Type(object):
    value = None

    def __init__(self, value):
        self.value = value


class UnaryOperation(object):
    operand = None
    operator = None  # AST operator

    def __init__(self, operand = None, operator = None):
        if operand is not None:
            self.operand = operand
        if operator is not None:
            self.operator = operator


class UniformDictionary(object):
    key = None
    value = None

    def __init__(self, key = None, value = None):
        if key is not None:
            self.key = key
        if value is not None:
            self.value = value


class UniformIterator(object):
    item = None

    def __init__(self, item = None):
        if item is not None:
            self.item = item


class UniformList(object):
    item = None

    def __init__(self, item = None):
        if item is not None:
            self.item = item


# Formula-specific classes


class Formula(object):
    pass


class FormulaFunctionDefinition(FunctionDefinition):
    def call_formula(self, state):
        node = self.node
        function_call = state.FunctionCall(definition = self)
        parameters = node.args
        positional_parameters = parameters.args[: len(parameters.args) - len(parameters.defaults)]
        for parameter in positional_parameters:
            parameter_name = parameter.id
            if parameter_name in ('_defaultP', '_P'):
                function_call.value_by_name[parameter_name] = state.LawNode(
                    is_reference = parameter_name == '_defaultP')
            elif parameter_name == 'period':
                function_call.value_by_name[parameter_name] = state.Period()
            elif parameter_name == 'self':
                function_call.value_by_name[parameter_name] = state.Formula()
            else:
                # Input variable
                if parameter_name.endswith('_holder'):
                    column_name = parameter_name[:-len('_holder')]
                    variable_value_class = state.DatedHolder
                else:
                    column_name = parameter_name
                    variable_value_class = state.Array
                column = state.tax_benefit_system.column_by_name.get(column_name)
                assert column is not None, u'{}@{}: Undefined input variable: {}'.format(
                    state.column.entity_key_plural, state.column.name, parameter_name)
                function_call.value_by_name[parameter_name] = variable_value_class(
                    column = column,
                    data_type = column.dtype,
                    entity_key_plural = column.entity_key_plural,
                    is_argument = True,
                    )

        if parameters.defaults:
            # Named parameters
            for parameter, value in itertools.izip(
                    parameters.args[len(parameters.args) - len(parameters.defaults):],
                    parameters.defaults,
                    ):
                assert isinstance(parameter, ast.Name), ast.dump(parameter)
                function_call.value_by_name[parameter.id] = conv.check(function_call.parse_value)(value, state)

        for statement in node.body:
            statement = conv.check(function_call.parse_statement)(statement, state)
            if isinstance(statement, state.Return):
                value = statement.operation
                assert isinstance(value, state.Array), "Unexpected return value {} in node {}".format(value,
                    ast.dump(node))
                data_type = value.data_type
                expected_data_type = state.column.dtype
                assert (
                    data_type == expected_data_type
                    or data_type == np.int32 and expected_data_type == np.float32
                    or data_type == np.int32 and expected_data_type == np.int16
                    ), "Formula returns an array of {} instead of {}".format(value.data_type, state.column.dtype)
                assert value.entity_key_plural == state.column.entity_key_plural, ast.dump(node)
                return value, None
        assert False, 'Missing return statement in formula: {}'.format(ast.dump(node))


class FormulaFunctionModule(FunctionModule):
    # Caution: This is not the whole module, but only a dummy "module" containing only the formula.
    def get_function_definition_class(self, state):
        return state.FormulaFunctionDefinition


# Default state


class State(conv.State):
    column = None  # Formula column
    Array = Array
    ArrayLength = ArrayLength
    BinaryOperation = BinaryOperation
    Continue = Continue
    Date = Date
    DateTime64 = DateTime64
    DatedHolder = DatedHolder
    Entity = Entity
    EntityToEntity = EntityToEntity
    Enum = Enum
    Formula = Formula
    FormulaFunctionDefinition = FormulaFunctionDefinition
    FormulaFunctionModule = FormulaFunctionModule
    FunctionCall = FunctionCall
    FunctionDefinition = FunctionDefinition
    FunctionModule = FunctionModule
    Holder = Holder
    Instant = Instant
    Lambda = Lambda
    LawNode = LawNode
    Logger = Logger
    Math = Math
    Module = Module
    Number = Number
    Period = Period
    Return = Return
    Simulation = Simulation
    String = String
    Structure = Structure
    tax_benefit_system = None
    TaxScalesTree = TaxScalesTree
    Type = Type
    UnaryOperation = UnaryOperation
    UniformDictionary = UniformDictionary
    UniformIterator = UniformIterator
    UniformList = UniformList
