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
import logging

from . import conv, periods, taxscales


log = logging.getLogger(__name__)
N_ = lambda message: message
units = [
    u'currency',
    u'day',
    u'hour',
    u'month',
    u'year',
    ]


class CompactNode(object):
    # Note: Attributes come from dated_node_json and are not defined in class.

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.__dict__))


class CompactRootNode(CompactNode, periods.PeriodMixin):
    pass


# Functions


def compact_dated_node_json(dated_node_json, code = None, period = None):
    node_type = dated_node_json['@type']
    if node_type == u'Node':
        if code is None:
            # Root node
            assert period is None, period
            compact_node = CompactRootNode()
            period_json = dated_node_json['period']
            compact_node.period = period = periods.period(period_json['unit'], period_json['start'],
                period_json['stop'])
        else:
            assert period is not None
            compact_node = CompactNode()
        compact_node_dict = compact_node.__dict__
        for key, value in dated_node_json['children'].iteritems():
            compact_node_dict[key] = compact_dated_node_json(value, code = key, period = period)
        return compact_node
    assert period is not None
    if node_type == u'Parameter':
        return dated_node_json.get('value')
    assert node_type == u'Scale'
    period_start_instant = periods.start_instant(period)
    period_stop_instant = periods.stop_instant(period)
    period_unit = periods.unit(period)
    if any('amount' in slice for slice in dated_node_json['slices']):
        # AmountTaxScale
        if periods.next_instant(period_unit, period_start_instant) > period_stop_instant:
            # Don't use an array for singletons, to simplify JSON and for compatibility with existing formulas.
            tax_scale = taxscales.AmountTaxScale(name = code, option = dated_node_json.get('option'))
            for dated_slice_json in dated_node_json['slices']:
                amount = dated_slice_json.get('amount')
                assert not isinstance(amount, list)
                threshold = dated_slice_json.get('threshold')
                assert not isinstance(threshold, list)
                if amount is not None and threshold is not None:
                    tax_scale.add_bracket(threshold, amount)
            return tax_scale
        tax_scales = [
            taxscales.AmountTaxScale(name = code, option = dated_node_json.get('option'))
            for instant in periods.iter(period)
            ]
        for dated_slice_json in dated_node_json['slices']:
            amounts = dated_slice_json.get('amount')
            if amount is None:
                continue
            assert isinstance(amounts, list)
            thresholds = dated_slice_json.get('threshold')
            if thresholds is None:
                continue
            assert isinstance(thresholds, list)
            for tax_scale, amount, threshold in itertools.izip(tax_scales, amounts, thresholds):
                if amount is not None and threshold is not None:
                    tax_scale.add_bracket(threshold, amount)
        return tax_scales

    # MarginalRateTaxScale
    if periods.next_instant(period_unit, period_start_instant) > period_stop_instant:
        # Don't use an array for singletons, to simplify JSON and for compatibility with existing formulas.
        tax_scale = taxscales.MarginalRateTaxScale(name = code, option = dated_node_json.get('option'))
        for dated_slice_json in dated_node_json['slices']:
            base = dated_slice_json.get('base', 1)
            assert not isinstance(base, list)
            rate = dated_slice_json.get('rate')
            assert not isinstance(rate, list)
            threshold = dated_slice_json.get('threshold')
            assert not isinstance(threshold, list)
            if rate is not None and threshold is not None:
                tax_scale.add_bracket(threshold, rate * base)
        return tax_scale
    tax_scales = [
        taxscales.MarginalRateTaxScale(name = code, option = dated_node_json.get('option'))
        for instant in periods.iter(period)
        ]
    default_bases = [
        1
        for instant in periods.iter(period)
        ]
    for dated_slice_json in dated_node_json['slices']:
        bases = dated_slice_json.get('base', default_bases)
        assert isinstance(bases, list)
        rates = dated_slice_json.get('rate')
        if rates is None:
            continue
        assert isinstance(rates, list)
        thresholds = dated_slice_json.get('threshold')
        if thresholds is None:
            continue
        assert isinstance(thresholds, list)
        for tax_scale, base, rate, threshold in itertools.izip(tax_scales, bases, rates, thresholds):
            if rate is not None and threshold is not None:
                tax_scale.add_bracket(threshold, rate * base)
    return tax_scales


def generate_dated_json_value(values_json, legislation_start_instant, legislation_stop_instant, period):
    max_stop_instant = None
    max_value = None
    min_start_instant = None
    min_value = None
    period_start_instant = periods.start_instant(period)
    period_stop_instant = periods.stop_instant(period)
    period_unit = periods.unit(period)
    value_by_instant = {}
    for value_json in values_json:
        _, value_start_instant, value_stop_instant = periods.period(period_unit, value_json['start'],
            value_json['stop'])
        if value_start_instant <= period_stop_instant and value_stop_instant >= period_start_instant:
            for value_instant in periods.iter_instants(period_unit, max(period_start_instant, value_start_instant),
                    min(period_stop_instant, value_stop_instant)):
                value_by_instant[value_instant] = value_json['value']
        if max_stop_instant is None or value_stop_instant > max_stop_instant:
            max_stop_instant = value_stop_instant
            max_value = value_json['value']
        if min_start_instant is None or value_start_instant < min_start_instant:
            min_start_instant = value_start_instant
            min_value = value_json['value']

    if (not value_by_instant or min(value_by_instant) > period_start_instant) \
            and period_start_instant < legislation_start_instant and min_start_instant is not None \
            and min_start_instant <= legislation_start_instant:
        # The requested date interval starts before the beginning of the legislation. Use the value of the first period,
        # when this period begins the same day or before the legislation.
        if not value_by_instant:
            value_stop_instant = period_stop_instant
        else:
            value_stop_instant = periods.previous_day_instant(min(value_by_instant))
        for value_instant in periods.iter_instants(period_unit, period_start_instant, value_stop_instant):
            value_by_instant[value_instant] = min_value

    if (not value_by_instant or max(value_by_instant) < period_stop_instant) \
            and period_stop_instant > legislation_stop_instant and max_stop_instant is not None \
            and max_stop_instant >= legislation_stop_instant:
        # The requested date interval stops after the end of the legislation. Use the value of the last period, when
        # this period ends the same day or after the legislation.
        if not value_by_instant:
            value_start_instant = period_start_instant
        else:
            value_start_instant = periods.next_day_instant(max(value_by_instant))
        for value_instant in periods.iter_instants(period_unit, value_start_instant, period_stop_instant):
            value_by_instant[value_instant] = max_value

    if periods.next_instant(period_unit, period_start_instant) > period_stop_instant:
        # Don't use an array for singletons, to simplify JSON and for compatibility with existing formulas.
        return value_by_instant.get(period_start_instant)
    value = [
        value_by_instant.get(instant)
        for instant in periods.iter(period)
        ]
    if all(item_value is None for item_value in value):
        return None
    return value


def generate_dated_legislation_json(legislation_json, period):
    period_unit = periods.unit(period)
    _, legislation_start_instant, legislation_stop_instant = periods.period(period_unit, legislation_json['start'],
        legislation_json['stop'])
    dated_legislation_json = generate_dated_node_json(
        legislation_json,
        legislation_start_instant,
        legislation_stop_instant,
        period,
        )
    dated_legislation_json['@context'] = u'http://openfisca.fr/contexts/dated-legislation.jsonld'
    dated_legislation_json['period'] = periods.json(period)
    return dated_legislation_json


def generate_dated_node_json(node_json, legislation_start_instant, legislation_stop_instant, period):
    dated_node_json = collections.OrderedDict()
    for key, value in node_json.iteritems():
        if key == 'children':
            # Occurs when @type == 'Node'.
            dated_children_json = type(value)(
                (child_code, dated_child_json)
                for child_code, dated_child_json in (
                    (
                        child_code,
                        generate_dated_node_json(child_json, legislation_start_instant, legislation_stop_instant,
                            period),
                        )
                    for child_code, child_json in value.iteritems()
                    )
                if dated_child_json is not None
                )
            if not dated_children_json:
                return None
            dated_node_json[key] = dated_children_json
        elif key in ('start', 'stop'):
            pass
        elif key == 'slices':
            # Occurs when @type == 'Scale'.
            dated_slices_json = [
                dated_slice_json
                for dated_slice_json in (
                    generate_dated_slice_json(slice_json, legislation_start_instant, legislation_stop_instant, period)
                    for slice_json in value
                    )
                if dated_slice_json is not None
                ]
            if not dated_slices_json:
                return None
            dated_node_json[key] = dated_slices_json
        elif key == 'values':
            # Occurs when @type == 'Parameter'.
            dated_value = generate_dated_json_value(value, legislation_start_instant, legislation_stop_instant, period)
            if dated_value is None:
                return None
            dated_node_json['value'] = dated_value
        else:
            dated_node_json[key] = value
    return dated_node_json


def generate_dated_slice_json(slice_json, legislation_start_instant, legislation_stop_instant, period):
    dated_slice_json = collections.OrderedDict()
    for key, value in slice_json.iteritems():
        if key in ('amount', 'base', 'rate', 'threshold'):
            dated_value = generate_dated_json_value(value, legislation_start_instant, legislation_stop_instant, period)
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
            if value_json['start'] > value_json['stop']:
                errors[index] = dict(to = state._(u"Last date must be greater than first date"))

        sorted_values_json = sorted(values_json, key = lambda value_json: value_json['start'], reverse = True)
        next_value_json = sorted_values_json[0]
        for index, value_json in enumerate(itertools.islice(sorted_values_json, 1, None)):
            next_date_str = (datetime.date(*(int(fragment) for fragment in value_json['stop'].split('-')))
                + datetime.timedelta(days = 1)).isoformat()
            if require_consecutive_dates and next_date_str < next_value_json['start']:
                errors.setdefault(index, {})['start'] = state._(u"Dates of values are not consecutive")
            elif next_date_str > next_value_json['start']:
                errors.setdefault(index, {})['start'] = state._(u"Dates of values overlap")
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
                period = conv.pipe(
                    conv.test_isinstance(dict),
                    conv.struct(
                        dict(
                            start = conv.pipe(
                                conv.test_isinstance(basestring),
                                conv.iso8601_input_to_date,
                                conv.date_to_iso8601_str,
                                conv.not_none,
                                ),
                            stop = conv.pipe(
                                conv.test_isinstance(basestring),
                                conv.iso8601_input_to_date,
                                conv.date_to_iso8601_str,
                                conv.not_none,
                                ),
                            unit = conv.pipe(
                                conv.test_isinstance(basestring),
                                conv.test_in((u"month", u"year")),
                                conv.not_none,
                                ),
                            ),
                        constructor = collections.OrderedDict,
                        drop_none_values = 'missing',
                        keep_value_order = True,
                        ),
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

    period = dated_legislation_json.pop('period')
    dated_legislation_json, error = validate_dated_node_json(dated_legislation_json, state = state)
    dated_legislation_json['period'] = period
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
                conv.item_or_sequence(
                    validate_dated_value_json,
                    ),
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
                validate_dated_slices_json_types,
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
                amount = conv.item_or_sequence(
                    validate_dated_value_json,
                    ),
                base = conv.item_or_sequence(
                    conv.pipe(
                        validate_dated_value_json,
                        conv.test_greater_or_equal(0),
                        ),
                    ),
                comment = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                rate = conv.item_or_sequence(
                    conv.pipe(
                        validate_dated_value_json,
                        conv.test_between(0, 1),
                        ),
                    ),
                threshold = conv.item_or_sequence(
                    conv.pipe(
                        validate_dated_value_json,
                        conv.test_greater_or_equal(0),
                        ),
                    ),
                ),
            constructor = collections.OrderedDict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(slice, state = state)
    conv.remove_ancestor_from_state(state, slice)
    return validated_slice, errors


def validate_dated_slices_json_types(slices, state = None):
    if not slices:
        return slices, None

    has_amount = any(
        'amount' in slice
        for slice in slices
        )
    if has_amount:
        if state is None:
            state = conv.default_state
        errors = {}
        for slice_index, slice in enumerate(slices):
            if 'base' in slice:
                errors.setdefault(slice_index, {})['base'] = state._(u"A scale can't contain both amounts and bases")
            if 'rate' in slice:
                errors.setdefault(slice_index, {})['rate'] = state._(u"A scale can't contain both amounts and rates")
        if errors:
            return slices, errors
    return slices, None


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
                'start': conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.iso8601_input_to_date,
                    conv.date_to_iso8601_str,
                    conv.not_none,
                    ),
                'stop': conv.pipe(
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

    start = legislation.pop('start')
    stop = legislation.pop('stop')
    legislation, error = validate_node_json(legislation, state = state)
    legislation['start'] = start
    legislation['stop'] = stop
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
                validate_slices_json_types,
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
                amount = validate_values_holder_json,
                base = validate_values_holder_json,
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
        conv.test(lambda slice: bool(slice.get('amount')) ^ bool(slice.get('rate')),
            error = N_(u"Either amount or rate must be provided")),
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
        for key in ('amount', 'base', 'rate', 'threshold'):
            valid_segments = []
            for value_json in (previous_slice.get(key) or []):
                from_date = datetime.date(*(int(fragment) for fragment in value_json['start'].split('-')))
                to_date = datetime.date(*(int(fragment) for fragment in value_json['stop'].split('-')))
                if valid_segments and valid_segments[-1][0] == to_date + datetime.timedelta(days = 1):
                    valid_segments[-1] = (from_date, valid_segments[-1][1])
                else:
                    valid_segments.append((from_date, to_date))
            for value_index, value_json in enumerate(slice.get(key) or []):
                from_date = datetime.date(*(int(fragment) for fragment in value_json['start'].split('-')))
                to_date = datetime.date(*(int(fragment) for fragment in value_json['stop'].split('-')))
                for valid_segment in valid_segments:
                    if valid_segment[0] <= from_date and to_date <= valid_segment[1]:
                        break
                else:
                    errors.setdefault(slice_index, {}).setdefault(key, {}).setdefault(value_index,
                        {})['start'] = state._(u"Dates don't belong to valid dates of previous slice")
        previous_slice = slice
    if errors:
        return slices, errors

    for slice_index, slice in enumerate(itertools.islice(slices, 1, None), 1):
        amount_segments = []
        for value_json in (slice.get('amount') or []):
            from_date = datetime.date(*(int(fragment) for fragment in value_json['start'].split('-')))
            to_date = datetime.date(*(int(fragment) for fragment in value_json['stop'].split('-')))
            if amount_segments and amount_segments[-1][0] == to_date + datetime.timedelta(days = 1):
                amount_segments[-1] = (from_date, amount_segments[-1][1])
            else:
                amount_segments.append((from_date, to_date))

        rate_segments = []
        for value_json in (slice.get('rate') or []):
            from_date = datetime.date(*(int(fragment) for fragment in value_json['start'].split('-')))
            to_date = datetime.date(*(int(fragment) for fragment in value_json['stop'].split('-')))
            if rate_segments and rate_segments[-1][0] == to_date + datetime.timedelta(days = 1):
                rate_segments[-1] = (from_date, rate_segments[-1][1])
            else:
                rate_segments.append((from_date, to_date))

        threshold_segments = []
        for value_json in (slice.get('threshold') or []):
            from_date = datetime.date(*(int(fragment) for fragment in value_json['start'].split('-')))
            to_date = datetime.date(*(int(fragment) for fragment in value_json['stop'].split('-')))
            if threshold_segments and threshold_segments[-1][0] == to_date + datetime.timedelta(days = 1):
                threshold_segments[-1] = (from_date, threshold_segments[-1][1])
            else:
                threshold_segments.append((from_date, to_date))

        for value_index, value_json in enumerate(slice.get('base') or []):
            from_date = datetime.date(*(int(fragment) for fragment in value_json['start'].split('-')))
            to_date = datetime.date(*(int(fragment) for fragment in value_json['stop'].split('-')))
            for rate_segment in rate_segments:
                if rate_segment[0] <= from_date and to_date <= rate_segment[1]:
                    break
            else:
                errors.setdefault(slice_index, {}).setdefault('base', {}).setdefault(value_index,
                    {})['start'] = state._(u"Dates don't belong to rate dates")

        for value_index, value_json in enumerate(slice.get('amount') or []):
            from_date = datetime.date(*(int(fragment) for fragment in value_json['start'].split('-')))
            to_date = datetime.date(*(int(fragment) for fragment in value_json['stop'].split('-')))
            for threshold_segment in threshold_segments:
                if threshold_segment[0] <= from_date and to_date <= threshold_segment[1]:
                    break
            else:
                errors.setdefault(slice_index, {}).setdefault('amount', {}).setdefault(value_index,
                    {})['start'] = state._(u"Dates don't belong to threshold dates")

        for value_index, value_json in enumerate(slice.get('rate') or []):
            from_date = datetime.date(*(int(fragment) for fragment in value_json['start'].split('-')))
            to_date = datetime.date(*(int(fragment) for fragment in value_json['stop'].split('-')))
            for threshold_segment in threshold_segments:
                if threshold_segment[0] <= from_date and to_date <= threshold_segment[1]:
                    break
            else:
                errors.setdefault(slice_index, {}).setdefault('rate', {}).setdefault(value_index,
                    {})['start'] = state._(u"Dates don't belong to threshold dates")

        for value_index, value_json in enumerate(slice.get('threshold') or []):
            from_date = datetime.date(*(int(fragment) for fragment in value_json['start'].split('-')))
            to_date = datetime.date(*(int(fragment) for fragment in value_json['stop'].split('-')))
            for amount_segment in amount_segments:
                if amount_segment[0] <= from_date and to_date <= amount_segment[1]:
                    break
            else:
                for rate_segment in rate_segments:
                    if rate_segment[0] <= from_date and to_date <= rate_segment[1]:
                        break
                else:
                    errors.setdefault(slice_index, {}).setdefault('threshold', {}).setdefault(value_index,
                        {})['start'] = state._(u"Dates don't belong to amount or rate dates")

    return slices, errors or None


def validate_slices_json_types(slices, state = None):
    if not slices:
        return slices, None

    has_amount = any(
        'amount' in slice
        for slice in slices
        )
    if has_amount:
        if state is None:
            state = conv.default_state
        errors = {}
        for slice_index, slice in enumerate(slices):
            if 'base' in slice:
                errors.setdefault(slice_index, {})['base'] = state._(u"A scale can't contain both amounts and bases")
            if 'rate' in slice:
                errors.setdefault(slice_index, {})['rate'] = state._(u"A scale can't contain both amounts and rates")
        if errors:
            return slices, errors
    return slices, None


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
                u'start': conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.iso8601_input_to_date,
                    conv.date_to_iso8601_str,
                    conv.not_none,
                    ),
                u'stop': conv.pipe(
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
