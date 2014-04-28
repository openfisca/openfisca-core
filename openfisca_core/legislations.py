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
from taxscales import TaxScale


N_ = lambda message: message
units = [
    u'currency',
    u'day',
    u'hour',
    u'month',
    u'year',
    ]


class CompactNode(object):
    datesim = None
    # Other attributes coming from dated_node_json are not defined in class.

    def __repr__(self):
        return 'CompactNode({})'.format(repr(self.__dict__))


# Functions


def compact_dated_node_json(dated_node_json, code = None):
    node_type = dated_node_json['@type']
    if node_type == u'Node':
        compact_node = CompactNode()
        if code is None:
            # Root node always contains a datesim.
            compact_node.datesim = datetime.date(*(int(fragment) for fragment in dated_node_json['datesim'].split('-')))
        compact_node_dict = compact_node.__dict__
        for key, value in dated_node_json['children'].iteritems():
            compact_node_dict[key] = compact_dated_node_json(value, code = key)
        return compact_node
    if node_type == u'Parameter':
        return dated_node_json.get('value')
    assert node_type == u'Scale'
    tax_scale = TaxScale(name = code, option = dated_node_json.get('option'))
    for dated_slice_json in dated_node_json['slices']:
        base = dated_slice_json.get('base', 1)
        constant_amount = dated_slice_json.get('constant_amount')
        rate = dated_slice_json.get('rate')
        threshold = dated_slice_json.get('threshold')
        if rate is not None and threshold is not None:
            tax_scale.add_bracket(threshold, rate * base)
        if constant_amount is not None and threshold is not None:
            tax_scale.add_bracket_constant_amount(threshold, constant_amount)
    tax_scale.marginal_to_average()
    return tax_scale


def generate_dated_json_value(values_json, date_str, from_str, to_str):
    max_to_str = None
    max_value = None
    min_from_str = None
    min_value = None
    for value_json in values_json:
        value_from_str = value_json['from']
        value_to_str = value_json['to']
        if value_from_str <= date_str <= value_to_str:
            return value_json['value']
        if max_to_str is None or value_to_str > max_to_str:
            max_to_str = value_to_str
            max_value = value_json['value']
        if min_from_str is None or value_from_str < min_from_str:
            min_from_str = value_from_str
            min_value = value_json['value']
    if date_str > to_str:
        # The requested date is after the end of the legislation. Use the value of the last period, when this
        # period ends the same day or after the legislation.
        if max_to_str is not None and max_to_str >= to_str:
            return max_value
    elif date_str < from_str:
        # The requested date is before the beginning of the legislation. Use the value of the first period, when this
        # period begins the same day or before the legislation.
        if min_from_str is not None and min_from_str <= from_str:
            return min_value
    return None


def generate_dated_legislation_json(legislation_json, date):
    date_str = date.isoformat()
    dated_legislation_json = generate_dated_node_json(legislation_json, date_str, legislation_json['from'],
        legislation_json['to'])
    dated_legislation_json['@context'] = 'http://openfisca.fr/contexts/dated-legislation.jsonld'
    dated_legislation_json['datesim'] = date_str
    return dated_legislation_json


def generate_dated_node_json(node_json, date_str, from_str, to_str):
    dated_node_json = collections.OrderedDict()
    for key, value in node_json.iteritems():
        if key == 'children':
            # Occurs when @type == 'Node'.
            dated_children_json = type(value)(
                (child_code, dated_child_json)
                for child_code, dated_child_json in (
                    (child_code, generate_dated_node_json(child_json, date_str, from_str, to_str))
                    for child_code, child_json in value.iteritems()
                    )
                if dated_child_json is not None
                )
            if not dated_children_json:
                return None
            dated_node_json[key] = dated_children_json
        elif key in ('from', 'to'):
            pass
        elif key == 'slices':
            # Occurs when @type == 'Scale'.
            dated_slices_json = [
                dated_slice_json
                for dated_slice_json in (
                    generate_dated_slice_json(slice_json, date_str, from_str, to_str)
                    for slice_json in value
                    )
                if dated_slice_json is not None
                ]
            if not dated_slices_json:
                return None
            dated_node_json[key] = dated_slices_json
        elif key == 'values':
            # Occurs when @type == 'Parameter'.
            dated_value = generate_dated_json_value(value, date_str, from_str, to_str)
            if dated_value is None:
                return None
            dated_node_json['value'] = dated_value
        else:
            dated_node_json[key] = value
    return dated_node_json


def generate_dated_slice_json(slice_json, date_str, from_str, to_str):
    dated_slice_json = collections.OrderedDict()
    for key, value in slice_json.iteritems():
        if key in ('base', 'constant_amount', 'rate', 'threshold'):
            dated_value = generate_dated_json_value(value, date_str, from_str, to_str)
            if dated_value is not None:
                dated_slice_json[key] = dated_value
        else:
            dated_slice_json[key] = value
    return dated_slice_json


# Level-1 Converters


def make_validate_values_json_dates(require_consecutive_dates = False):
    def validate_values_json_dates(values_json, state = None):
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
            if require_consecutive_dates and next_date_str < next_value_json['from']:
                errors.setdefault(index, {})['from'] = state._(u"Dates of values are not consecutive")
            elif next_date_str > next_value_json['from']:
                errors.setdefault(index, {})['from'] = state._(u"Dates of values overlap")
            next_value_json = value_json

        return sorted_values_json, errors or None

    return validate_values_json_dates


def validate_dated_legislation_json(dated_legislation_json, state = None):
    if dated_legislation_json is None:
        return None, None
    if state is None:
        state = conv.default_state

    dated_legislation_json, error = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            dict(
                datesim = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.iso8601_input_to_date,
                    conv.date_to_iso8601_str,
                    conv.not_none,
                    ),
                ),
            constructor = collections.OrderedDict,
            default = conv.noop,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(dated_legislation_json, state = state)
    if error is not None:
        return dated_legislation_json, error

    datesim = dated_legislation_json.pop('datesim')
    dated_legislation_json, error = validate_dated_node_json(dated_legislation_json, state = state)
    dated_legislation_json['datesim'] = datesim
    return dated_legislation_json, error


def validate_dated_node_json(node, state = None):
    if node is None:
        return None, None
    state = conv.add_ancestor_to_state(state, node)

    validated_node, error = conv.test_isinstance(dict)(node, state = state)
    if error is not None:
        conv.remove_ancestor_from_state(state, node)
        return validated_node, error

    validated_node, errors = conv.struct(
        {
            '@context': conv.pipe(
                conv.test_isinstance(basestring),
                conv.make_input_to_url(full = True),
                conv.test_equals(u'http://openfisca.fr/contexts/dated-legislation.jsonld'),
                ),
            '@type': conv.pipe(
                conv.test_isinstance(basestring),
                conv.cleanup_line,
                conv.test_in((u'Node', u'Parameter', u'Scale')),
                conv.not_none,
                ),
            'comment': conv.pipe(
                conv.test_isinstance(basestring),
                conv.cleanup_text,
                ),
            'description': conv.pipe(
                conv.test_isinstance(basestring),
                conv.cleanup_line,
                ),
            },
        constructor = collections.OrderedDict,
        default = conv.noop,
        drop_none_values = 'missing',
        keep_value_order = True,
        )(validated_node, state = state)
    if errors is not None:
        conv.remove_ancestor_from_state(state, node)
        return validated_node, errors

    validated_node.pop('@context', None)  # Remove optional @context everywhere. It will be added to root node later.
    node_converters = {
        '@type': conv.noop,
        'comment': conv.noop,
        'description': conv.noop,
        }
    node_type = validated_node['@type']
    if node_type == u'Node':
        node_converters.update(dict(
            children = conv.pipe(
                conv.test_isinstance(dict),
                conv.uniform_mapping(
                    conv.pipe(
                        conv.test_isinstance(basestring),
                        conv.cleanup_line,
                        conv.not_none,
                        ),
                    conv.pipe(
                        validate_dated_node_json,
                        conv.not_none,
                        ),
                    ),
                conv.empty_to_none,
                conv.not_none,
                ),
            ))
    elif node_type == u'Parameter':
        node_converters.update(dict(
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
            value = conv.pipe(
                validate_dated_value_json,
                conv.not_none,
                ),
            ))
    else:
        assert node_type == u'Scale'
        node_converters.update(dict(
            option = conv.pipe(
                conv.test_isinstance(basestring),
                conv.input_to_slug,
                conv.test_in((
                    'contrib',
                    'main-d-oeuvre',
                    'noncontrib',
                    )),
                ),
            slices = conv.pipe(
                conv.test_isinstance(list),
                conv.uniform_sequence(
                    validate_dated_slice_json,
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
            ))
    validated_node, errors = conv.struct(
        node_converters,
        constructor = collections.OrderedDict,
        drop_none_values = 'missing',
        keep_value_order = True,
        )(validated_node, state = state)

    conv.remove_ancestor_from_state(state, node)
    return validated_node, errors


def validate_dated_slice_json(slice, state = None):
    if slice is None:
        return None, None
    state = conv.add_ancestor_to_state(state, slice)
    validated_slice, errors = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            dict(
                base = conv.pipe(
                    validate_dated_value_json,
                    conv.test_greater_or_equal(0),
                    ),
                constant_amount = validate_dated_value_json,
                comment = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                rate = conv.pipe(
                    validate_dated_value_json,
                    conv.test_between(0, 1),
                    ),
                threshold = conv.pipe(
                    validate_dated_value_json,
                    conv.test_greater_or_equal(0),
                    ),
                ),
            constructor = collections.OrderedDict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(slice, state = state)
    conv.remove_ancestor_from_state(state, slice)
    return validated_slice, errors


def validate_dated_value_json(value, state = None):
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
    return value_converter(value, state = state or conv.default_state)


def validate_legislation_json(legislation, state = None):
    if legislation is None:
        return None, None
    if state is None:
        state = conv.default_state

    legislation, error = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            {
                'from': conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.iso8601_input_to_date,
                    conv.date_to_iso8601_str,
                    conv.not_none,
                    ),
                'to': conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.iso8601_input_to_date,
                    conv.date_to_iso8601_str,
                    conv.not_none,
                    ),
                },
            constructor = collections.OrderedDict,
            default = conv.noop,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(legislation, state = state)
    if error is not None:
        return legislation, error

    saved_from = legislation.pop('from')
    saved_to = legislation.pop('to')
    legislation, error = validate_node_json(legislation, state = state)
    legislation['from'] = saved_from
    legislation['to'] = saved_to
    return legislation, error


def validate_node_json(node, state = None):
    if node is None:
        return None, None
    state = conv.add_ancestor_to_state(state, node)

    validated_node, error = conv.test_isinstance(dict)(node, state = state)
    if error is not None:
        conv.remove_ancestor_from_state(state, node)
        return validated_node, error

    validated_node, errors = conv.struct(
        {
            '@context': conv.pipe(
                conv.test_isinstance(basestring),
                conv.make_input_to_url(full = True),
                conv.test_equals(u'http://openfisca.fr/contexts/legislation.jsonld'),
                ),
            '@type': conv.pipe(
                conv.test_isinstance(basestring),
                conv.cleanup_line,
                conv.test_in((u'Node', u'Parameter', u'Scale')),
                conv.not_none,
                ),
            'comment': conv.pipe(
                conv.test_isinstance(basestring),
                conv.cleanup_text,
                ),
            'description': conv.pipe(
                conv.test_isinstance(basestring),
                conv.cleanup_line,
                ),
            },
        constructor = collections.OrderedDict,
        default = conv.noop,
        drop_none_values = 'missing',
        keep_value_order = True,
        )(validated_node, state = state)
    if errors is not None:
        conv.remove_ancestor_from_state(state, node)
        return validated_node, errors

    validated_node.pop('@context', None)  # Remove optional @context everywhere. It will be added to root node later.
    node_converters = {
        '@type': conv.noop,
        'comment': conv.noop,
        'description': conv.noop,
        }
    node_type = validated_node['@type']
    if node_type == u'Node':
        node_converters.update(dict(
            children = conv.pipe(
                conv.test_isinstance(dict),
                conv.uniform_mapping(
                    conv.pipe(
                        conv.test_isinstance(basestring),
                        conv.cleanup_line,
                        conv.not_none,
                        ),
                    conv.pipe(
                        validate_node_json,
                        conv.not_none,
                        ),
                    ),
                conv.empty_to_none,
                conv.not_none,
                ),
            ))
    elif node_type == u'Parameter':
        node_converters.update(dict(
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
                make_validate_values_json_dates(require_consecutive_dates = True),
                conv.empty_to_none,
                conv.not_none,
                ),
            ))
    else:
        assert node_type == u'Scale'
        node_converters.update(dict(
            option = conv.pipe(
                conv.test_isinstance(basestring),
                conv.input_to_slug,
                conv.test_in((
                    'contrib',
                    'main-d-oeuvre',
                    'noncontrib',
                    )),
                ),
            slices = conv.pipe(
                conv.test_isinstance(list),
                conv.uniform_sequence(
                    validate_slice_json,
                    drop_none_items = True,
                    ),
                validate_slices_json_dates,
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
            ))
    validated_node, errors = conv.struct(
        node_converters,
        constructor = collections.OrderedDict,
        drop_none_values = 'missing',
        keep_value_order = True,
        )(validated_node, state = state)

    conv.remove_ancestor_from_state(state, node)
    return validated_node, errors


def validate_slice_json(slice, state = None):
    if slice is None:
        return None, None
    state = conv.add_ancestor_to_state(state, slice)
    validated_slice, errors = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            dict(
                base = validate_values_holder_json,
                constant_amount = validate_values_holder_json,
                comment = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                rate = validate_values_holder_json,
                threshold = conv.pipe(
                    validate_values_holder_json,
                    conv.not_none,
                    ),
                ),
            constructor = collections.OrderedDict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        conv.test(lambda slice: bool(slice.get('constant_amount')) ^ bool(slice.get('rate')),
            error = N_(u"Either constant_amount or rate must be provided")),
        )(slice, state = state)
    conv.remove_ancestor_from_state(state, slice)
    return validated_slice, errors


def validate_slices_json_dates(slices, state = None):
    if not slices:
        return slices, None
    if state is None:
        state = conv.default_state
    errors = {}

    previous_slice = slices[0]
    for slice_index, slice in enumerate(itertools.islice(slices, 1, None), 1):
        for key in ('base', 'constant_amount', 'rate', 'threshold'):
            valid_segments = []
            for value_json in (previous_slice.get(key) or []):
                from_date = datetime.date(*(int(fragment) for fragment in value_json['from'].split('-')))
                to_date = datetime.date(*(int(fragment) for fragment in value_json['to'].split('-')))
                if valid_segments and valid_segments[-1][0] == to_date + datetime.timedelta(days = 1):
                    valid_segments[-1] = (from_date, valid_segments[-1][1])
                else:
                    valid_segments.append((from_date, to_date))
            for value_index, value_json in enumerate(slice.get(key) or []):
                from_date = datetime.date(*(int(fragment) for fragment in value_json['from'].split('-')))
                to_date = datetime.date(*(int(fragment) for fragment in value_json['to'].split('-')))
                for valid_segment in valid_segments:
                    if valid_segment[0] <= from_date and to_date <= valid_segment[1]:
                        break
                else:
                    errors.setdefault(slice_index, {}).setdefault(key, {}).setdefault(value_index,
                        {})['from'] = state._(u"Dates don't belong to valid dates of previous slice")
        previous_slice = slice
    if errors:
        return slices, errors

    for slice_index, slice in enumerate(itertools.islice(slices, 1, None), 1):
        constant_amount_segments = []
        for value_json in (slice.get('constant_amount') or []):
            from_date = datetime.date(*(int(fragment) for fragment in value_json['from'].split('-')))
            to_date = datetime.date(*(int(fragment) for fragment in value_json['to'].split('-')))
            if constant_amount_segments and constant_amount_segments[-1][0] == to_date + datetime.timedelta(days = 1):
                constant_amount_segments[-1] = (from_date, constant_amount_segments[-1][1])
            else:
                constant_amount_segments.append((from_date, to_date))

        rate_segments = []
        for value_json in (slice.get('rate') or []):
            from_date = datetime.date(*(int(fragment) for fragment in value_json['from'].split('-')))
            to_date = datetime.date(*(int(fragment) for fragment in value_json['to'].split('-')))
            if rate_segments and rate_segments[-1][0] == to_date + datetime.timedelta(days = 1):
                rate_segments[-1] = (from_date, rate_segments[-1][1])
            else:
                rate_segments.append((from_date, to_date))

        threshold_segments = []
        for value_json in (slice.get('threshold') or []):
            from_date = datetime.date(*(int(fragment) for fragment in value_json['from'].split('-')))
            to_date = datetime.date(*(int(fragment) for fragment in value_json['to'].split('-')))
            if threshold_segments and threshold_segments[-1][0] == to_date + datetime.timedelta(days = 1):
                threshold_segments[-1] = (from_date, threshold_segments[-1][1])
            else:
                threshold_segments.append((from_date, to_date))

        for value_index, value_json in enumerate(slice.get('base') or []):
            from_date = datetime.date(*(int(fragment) for fragment in value_json['from'].split('-')))
            to_date = datetime.date(*(int(fragment) for fragment in value_json['to'].split('-')))
            for rate_segment in rate_segments:
                if rate_segment[0] <= from_date and to_date <= rate_segment[1]:
                    break
            else:
                errors.setdefault(slice_index, {}).setdefault('base', {}).setdefault(value_index,
                    {})['from'] = state._(u"Dates don't belong to rate dates")

        for value_index, value_json in enumerate(slice.get('constant_amount') or []):
            from_date = datetime.date(*(int(fragment) for fragment in value_json['from'].split('-')))
            to_date = datetime.date(*(int(fragment) for fragment in value_json['to'].split('-')))
            for threshold_segment in threshold_segments:
                if threshold_segment[0] <= from_date and to_date <= threshold_segment[1]:
                    break
            else:
                errors.setdefault(slice_index, {}).setdefault('constant_amount', {}).setdefault(value_index,
                    {})['from'] = state._(u"Dates don't belong to threshold dates")

        for value_index, value_json in enumerate(slice.get('rate') or []):
            from_date = datetime.date(*(int(fragment) for fragment in value_json['from'].split('-')))
            to_date = datetime.date(*(int(fragment) for fragment in value_json['to'].split('-')))
            for threshold_segment in threshold_segments:
                if threshold_segment[0] <= from_date and to_date <= threshold_segment[1]:
                    break
            else:
                errors.setdefault(slice_index, {}).setdefault('rate', {}).setdefault(value_index,
                    {})['from'] = state._(u"Dates don't belong to threshold dates")

        for value_index, value_json in enumerate(slice.get('threshold') or []):
            from_date = datetime.date(*(int(fragment) for fragment in value_json['from'].split('-')))
            to_date = datetime.date(*(int(fragment) for fragment in value_json['to'].split('-')))
            for constant_amount_segment in constant_amount_segments:
                if constant_amount_segment[0] <= from_date and to_date <= constant_amount_segment[1]:
                    break
            else:
                for rate_segment in rate_segments:
                    if rate_segment[0] <= from_date and to_date <= rate_segment[1]:
                        break
                else:
                    errors.setdefault(slice_index, {}).setdefault('threshold', {}).setdefault(value_index,
                        {})['from'] = state._(u"Dates don't belong to rate or constant_amount dates")

    return slices, errors or None


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


validate_values_holder_json = conv.pipe(
    conv.test_isinstance(list),
    conv.uniform_sequence(
        validate_value_json,
        drop_none_items = True,
        ),
    make_validate_values_json_dates(require_consecutive_dates = False),
    conv.empty_to_none,
    )


# Level-2 Converters


validate_any_legislation_json = conv.pipe(
    conv.test_isinstance(dict),
    conv.condition(
        conv.test(lambda legislation_json: 'datesim' in legislation_json),
        validate_dated_legislation_json,
        validate_legislation_json,
        ),
    )
