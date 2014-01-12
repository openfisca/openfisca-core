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


"""Handle legislative parameters in JSON format."""


import collections
import datetime
import itertools

from . import conv


units = [
    u'currency',
    u'day',
    u'hour',
    u'month',
    u'year',
    ]


def generate_dated_json_value(values_json, date_str):
    for value_json in values_json:
        if value_json['from'] <= date_str <= value_json['to']:
            return value_json['value']
    return None


def generate_dated_node_json(node_json, date_str):
    dated_node_json = collections.OrderedDict()
    for key, value in node_json.iteritems():
        if key == 'nodes':
            dated_node_json[key] = [
                generate_dated_node_json(item, date_str)
                for item in value
                ]
        elif key == 'parameters':
            dated_node_json[key] = [
                generate_dated_parameter_json(item, date_str)
                for item in value
                ]
        elif key == 'scales':
            dated_node_json[key] = [
                generate_dated_scale_json(item, date_str)
                for item in value
                ]
        else:
            dated_node_json[key] = value
    return dated_node_json


def generate_dated_parameter_json(parameter_json, date_str):
    dated_parameter_json = collections.OrderedDict()
    for key, value in parameter_json.iteritems():
        if key == 'parameters':
            dated_parameter_json[key] = [
                generate_dated_parameter_json(item, date_str)
                for item in value
                ]
        elif key == 'values':
            dated_parameter_json['value'] = generate_dated_json_value(value, date_str)
        else:
            dated_parameter_json[key] = value
    return dated_parameter_json


def generate_dated_scale_json(scale_json, date_str):
    dated_scale_json = collections.OrderedDict()
    for key, value in scale_json.iteritems():
        if key == 'slices':
            dated_scale_json[key] = [
                generate_dated_slice_json(item, date_str)
                for item in value
                ]
        else:
            dated_scale_json[key] = value
    return dated_scale_json


def generate_dated_slice_json(slice_json, date_str):
    dated_slice_json = collections.OrderedDict()
    for key, value in slice_json.iteritems():
        if key in ('base', 'rate', 'threshold'):
            dated_slice_json[key] = generate_dated_json_value(value, date_str)
        else:
            dated_slice_json[key] = value
    return dated_slice_json


def validate_node_json(node, state = None):
    if node is None:
        return None, None
    state = conv.add_ancestor_to_state(state, node)
    validated_node, errors = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            dict(
                code = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_line,
                    conv.not_none,
                    ),
                comment = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                description = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_line,
                    ),
                nodes = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        validate_node_json,
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    ),
                parameters = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        validate_parameter_json,
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    ),
                scales = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        validate_scale_json,
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    ),
                ),
            constructor = collections.OrderedDict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(node, state = state)
    if errors is None:
        required_group_keys = ('nodes', 'parameters', 'scales')
        if all(
                validated_node.get(key) is None
                for key in required_group_keys
                ):
            error = state._(u"At least one of the following items must be present: {}").format(state._(u', ').join(
                u'"{}"'.format(key)
                for key in required_group_keys
                ))
            errors = dict(
                (key, error)
                for key in required_group_keys
                )
    conv.remove_ancestor_from_state(state, node)
    return validated_node, errors


def validate_parameter_json(parameter, state = None):
    if parameter is None:
        return None, None
    state = conv.add_ancestor_to_state(state, parameter)
    validated_parameter, errors = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            dict(
                code = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_line,
                    conv.not_none,
                    ),
                comment = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                description = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_line,
                    ),
                format = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.input_to_slug,
                    conv.test_in([
                        'boolean',
                        'float',
                        'integer',
                        'rate',
                        ]),
                    ),
                unit = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.input_to_slug,
                    conv.test_in(units),
                    ),
                values = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        validate_value_json,
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    conv.not_none,
                    ),
                ),
            constructor = collections.OrderedDict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(parameter, state = state)
    conv.remove_ancestor_from_state(state, parameter)
    return validated_parameter, errors


def validate_scale_json(scale, state = None):
    if scale is None:
        return None, None
    state = conv.add_ancestor_to_state(state, scale)
    validated_scale, errors = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            dict(
                code = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_line,
                    conv.not_none,
                    ),
                comment = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                description = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_line,
                    ),
                option = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.input_to_slug,
                    conv.test_in((
                        'contrib',
                        'noncontrib',
                        )),
                    ),
                slices = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        validate_slice_json,
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    conv.not_none,
                    ),
                unit = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.input_to_slug,
                    conv.test_in((
                        'currency',
                        )),
                    ),
                ),
            constructor = collections.OrderedDict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(scale, state = state)
    conv.remove_ancestor_from_state(state, scale)
    return validated_scale, errors


def validate_slice_json(slice, state = None):
    if slice is None:
        return None, None
    state = conv.add_ancestor_to_state(state, slice)
    validated_slice, errors = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            dict(
                base = validate_values_holder_json,
                comment = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                rate = conv.pipe(
                    validate_values_holder_json,
                    conv.not_none,
                    ),
                threshold = conv.pipe(
                    validate_values_holder_json,
                    conv.not_none,
                    ),
                ),
            constructor = collections.OrderedDict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(slice, state = state)
    conv.remove_ancestor_from_state(state, slice)
    return validated_slice, errors


def validate_value_json(value, state = None):
    if value is None:
        return None, None
    container = state.ancestors[-1]
    value_converter = dict(
        boolean = conv.condition(
            conv.test_isinstance(int),
            conv.test_in((0, 1)),
            conv.test_isinstance(bool),
            ),
        float = conv.condition(
            conv.test_isinstance(int),
            conv.anything_to_float,
            conv.test_isinstance(float),
            ),
        integer = conv.condition(
            conv.test_isinstance(float),
            conv.pipe(
                conv.test(lambda number: round(number) == number),
                conv.function(int),
                ),
            conv.test_isinstance(int),
            ),
        rate = conv.condition(
            conv.test_isinstance(int),
            conv.anything_to_float,
            conv.test_isinstance(float),
            ),
        )[container.get('format') or 'float']  # Only parameters have a "format".
    state = conv.add_ancestor_to_state(state, value)
    validated_value, errors = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            {
                u'comment': conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                u'from': conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.iso8601_input_to_date,
                    conv.date_to_iso8601_str,
                    conv.not_none,
                    ),
                u'to': conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.iso8601_input_to_date,
                    conv.date_to_iso8601_str,
                    conv.not_none,
                    ),
                u'value': conv.pipe(
                    value_converter,
                    conv.not_none,
                    ),
                },
            constructor = collections.OrderedDict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(value, state = state)
    conv.remove_ancestor_from_state(state, value)
    return validated_value, errors


def validate_values_json_date(values_json, state = None):
    if not values_json:
        return values_json, None
    if state is None:
        state = conv.default_state

    errors = {}
    for index, value_json in enumerate(values_json):
        if value_json['from'] > value_json['to']:
            errors[index] = dict(to = state._(u"Last date must be greater than first date"))

    sorted_values_json = sorted(values_json, key = lambda value_json: value_json['from'], reverse = True)
    next_value_json = sorted_values_json[0]
    for index, value_json in enumerate(itertools.islice(sorted_values_json, 1, None)):
        next_date_str = (datetime.date(*(int(fragment) for fragment in value_json['to'].split('-')))
            + datetime.timedelta(days = 1)).isoformat()
        if next_date_str < next_value_json['from']:
            errors.setdefault(index, {})['from'] = state._(u"Dates of values are not consecutive")
        elif next_date_str > next_value_json['from']:
            errors.setdefault(index, {})['from'] = state._(u"Dates of values overlap")
        next_value_json = value_json

    return sorted_values_json, errors or None


validate_values_holder_json = conv.pipe(
    conv.test_isinstance(list),
    conv.uniform_sequence(
        validate_value_json,
        drop_none_items = True,
        ),
    validate_values_json_date,
    conv.empty_to_none,
    )
