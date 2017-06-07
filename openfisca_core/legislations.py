# -*- coding: utf-8 -*-


"""Handle legislative parameters in JSON format."""


import logging

from . import conv, periods, taxscales


def N_(message):
    return message


log = logging.getLogger(__name__)
units = [
    u'currency',
    u'day',
    u'hour',
    u'month',
    u'year',
    ]


class ParameterNotFound(Exception):
    def __init__(self, name, instant, variable_name = None):
        assert name is not None
        assert instant is not None
        self.name = name
        self.instant = instant
        self.variable_name = variable_name
        message = u'Legislation parameter "{}" was not found at instant "{}"'.format(name, instant)
        if variable_name is not None:
            message += u' by variable "{}"'.format(variable_name)
        super(ParameterNotFound, self).__init__(message)

    def to_json(self):
        self_json = {
            'instant': unicode(self.instant),
            'message': unicode(self),
            'parameter_name': self.name,
            }
        if self.variable_name is not None:
            self_json['variable_name'] = self.variable_name
        return self_json


class CompactNode(object):
    # Note: Legislation attributes are set explicitely by compact_dated_node_json
    # (ie they are not computed by a magic method).

    instant = None
    name = None

    def __delitem__(self, key):
        del self.__dict__[key]

    # Reminder: __getattr__ is called only when attribute is not found.
    def __getattr__(self, key):
        name = u'.'.join([self.name, key]) \
            if self.name is not None \
            else key
        raise ParameterNotFound(
            instant = self.instant,
            name = name,
            )

    def __getitem__(self, key):
        return self.__dict__[key]

    def __init__(self, instant, name = None):
        assert instant is not None
        self.instant = instant
        self.name = name

    def __iter__(self):
        return self.__dict__.iterkeys()

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.__dict__))

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def combine_tax_scales(self):
        """Combine all the MarginalRateTaxScales in the node into a single MarginalRateTaxScale."""
        combined_tax_scales = None
        for name, child in self.iteritems():
            if name == 'name' or name == 'instant':
                continue
            if not isinstance(child, taxscales.AbstractTaxScale):
                log.info(u'Skipping {} with value {} because it is not a tax scale'.format(name, child))
                continue

            if combined_tax_scales is None:
                combined_tax_scales = taxscales.MarginalRateTaxScale(name = name)
                combined_tax_scales.add_bracket(0, 0)
            combined_tax_scales.add_tax_scale(child)
        return combined_tax_scales

    def copy(self, deep = False):
        new = self.__class__()
        for name, value in self.iteritems():
            if deep:
                if isinstance(value, CompactNode):
                    new[name] = value.copy(deep = deep)
                elif isinstance(value, taxscales.AbstractTaxScale):
                    new[name] = value.copy()
                else:
                    new[name] = value
            else:
                new[name] = value
        return new

    def get(self, key, default = None):
        return self.__dict__.get(key, default)

    def items(self):
        return self.__dict__.items()

    def iteritems(self):
        return self.__dict__.iteritems()

    def iterkeys(self):
        return self.__dict__.iterkeys()

    def itervalues(self):
        return self.__dict__.itervalues()

    def keys(self):
        return self.__dict__.keys()

    def pop(self, key, default = None):
        return self.__dict__.pop(key, default)

    def scale_tax_scales(self, factor):
        """Scale all the MarginalRateTaxScales in the node."""
        scaled_node = CompactNode()
        for key, child in self.iteritems():
            scaled_node[key] = child.scale_tax_scales(factor)
        return scaled_node

    def update(self, value):
        if isinstance(value, CompactNode):
            value = value.__dict__
        return self.__dict__.update(value)

    def values(self):
        return self.__dict__.values()


class TracedCompactNode(object):
    """
    A proxy for CompactNode which stores the a simulation instance. Used for simulations with trace mode enabled.

    Overload __delitem__, __getitem__ and __setitem__ even if __getattribute__ is defined because of:
    https://stackoverflow.com/questions/11360020/why-is-getattribute-not-invoked-on-an-implicit-getitem-invocation
    """
    compact_node = None
    simulation = None
    traced_attributes_name = None

    def __init__(self, compact_node, simulation, traced_attributes_name):
        self.compact_node = compact_node
        self.simulation = simulation
        self.traced_attributes_name = traced_attributes_name

    def __delitem__(self, key):
        del self.compact_node.__dict__[key]

    # Reminder: __getattr__ is called only when attribute is not found.
    def __getattr__(self, key):
        value = getattr(self.compact_node, key)
        if key in self.traced_attributes_name:
            calling_frame = self.simulation.stack_trace[-1]
            caller_parameters_infos = calling_frame['parameters_infos']
            parameter_name = u'.'.join([self.compact_node.name, key]) \
                if self.compact_node.name is not None \
                else key
            parameter_infos = {
                "instant": str(self.compact_node.instant),
                "name": parameter_name,
                }
            if isinstance(value, taxscales.AbstractTaxScale):
                # Do not serialize value in JSON for tax scales since they are too big.
                parameter_infos["@type"] = "Scale"
            else:
                parameter_infos.update({"@type": "Parameter", "value": value})
            if parameter_infos not in caller_parameters_infos:
                caller_parameters_infos.append(dict(sorted(parameter_infos.iteritems())))
        return value

    def __getitem__(self, key):
        return self.compact_node.__dict__[key]

    def __setitem__(self, key, value):
        self.compact_node.__dict__[key] = value


# Functions


def compact_dated_node_json(dated_node_json, code = None, instant = None, parent_codes = None,
        traced_simulation = None):
    """
    Compacts a dated node JSON into a hierarchy of CompactNode objects.

    The "traced_simulation" argument can be used for simulations with trace mode enabled, this stores parameter values
    in the traceback.
    """
    node_type = dated_node_json['@type']
    if node_type == u'Node':
        if code is None:
            # Root node
            assert instant is None, instant
            instant = periods.instant(dated_node_json['instant'])
        assert instant is not None
        name = u'.'.join((parent_codes or []) + [code]) \
            if code is not None \
            else None
        compact_node = CompactNode(instant = instant, name = name)
        for key, value in dated_node_json['children'].iteritems():
            child_parent_codes = None
            if traced_simulation is not None:
                child_parent_codes = [] if parent_codes is None else parent_codes[:]
                if code is not None:
                    child_parent_codes += [code]
                child_parent_codes = child_parent_codes or None
            compact_node.__dict__[key] = compact_dated_node_json(
                value,
                code = key,
                instant = instant,
                parent_codes = child_parent_codes,
                traced_simulation = traced_simulation,
                )
        if traced_simulation is not None:
            traced_children_code = [
                key
                for key, value in dated_node_json['children'].iteritems()
                if value['@type'] != u'Node'
                ]
            # Only trace Nodes which have at least one Parameter child.
            if traced_children_code:
                compact_node = TracedCompactNode(
                    compact_node = compact_node,
                    simulation = traced_simulation,
                    traced_attributes_name = traced_children_code,
                    )
        return compact_node
    assert instant is not None
    if node_type == u'Parameter':
        return dated_node_json.get('value')
    assert node_type == u'Scale'
    if any('amount' in bracket for bracket in dated_node_json['brackets']):
        # AmountTaxScale
        tax_scale = taxscales.AmountTaxScale(name = code, option = dated_node_json.get('option'))
        for dated_bracket_json in dated_node_json['brackets']:
            amount = dated_bracket_json.get('amount')
            assert not isinstance(amount, list)
            threshold = dated_bracket_json.get('threshold')
            assert not isinstance(threshold, list)
            if amount is not None and threshold is not None:
                tax_scale.add_bracket(threshold, amount)
        return tax_scale

    rates_kind = dated_node_json.get('rates_kind', None)
    if rates_kind == "average":
        # LinearAverageRateTaxScale
        tax_scale = taxscales.LinearAverageRateTaxScale(
            name = code,
            option = dated_node_json.get('option'),
            unit = dated_node_json.get('unit'),
            )
    else:
        # MarginalRateTaxScale
        tax_scale = taxscales.MarginalRateTaxScale(name = code, option = dated_node_json.get('option'))

    for dated_bracket_json in dated_node_json['brackets']:
        base = dated_bracket_json.get('base', 1)
        assert not isinstance(base, list)
        rate = dated_bracket_json.get('rate')
        assert not isinstance(rate, list)
        threshold = dated_bracket_json.get('threshold')
        assert not isinstance(threshold, list)
        if rate is not None and threshold is not None:
            tax_scale.add_bracket(threshold, rate * base)
    return tax_scale


def generate_dated_bracket_json(bracket_json, instant_str):
    dated_bracket_json = dict()
    for key, value in bracket_json.iteritems():
        if key in ('amount', 'base', 'rate', 'threshold'):
            dated_value = generate_dated_json_value(value, instant_str)
            if dated_value is not None:
                dated_bracket_json[key] = dated_value
        else:
            dated_bracket_json[key] = value
    return dated_bracket_json


def generate_dated_json_value(values_json, instant):
    for value_json in values_json:
        value_start = value_json.get('start')
        if value_start <= instant:
            if 'value' in value_json:
                return value_json['value']
            else:
                return None
    return None


def generate_dated_legislation_json(legislation_json, instant):
    instant_str = str(periods.instant(instant))
    dated_legislation_json = generate_dated_node_json(legislation_json, instant_str)
    if dated_legislation_json is None:  # special case when the legislation is empty
        dated_legislation_json = dict({
            '@type': u'Node',
            'children': dict(),
            })
    dated_legislation_json['@context'] = u'https://openfisca.fr/contexts/dated-legislation.jsonld'
    dated_legislation_json['instant'] = instant_str
    return dated_legislation_json


def generate_dated_node_json(node_json, instant_str):
    dated_node_json = dict()
    for key, value in node_json.iteritems():
        if key == 'children':
            # Occurs when @type == 'Node'.
            dated_children_json = type(value)(
                (child_code, dated_child_json)
                for child_code, dated_child_json in (
                    (
                        child_code,
                        generate_dated_node_json(child_json, instant_str),
                        )
                    for child_code, child_json in value.iteritems()
                    )
                if dated_child_json is not None
                )
            if not dated_children_json:
                return None
            dated_node_json[key] = dated_children_json
        elif key in ('start', ):
            pass
        elif key == 'brackets':
            # Occurs when @type == 'Scale'.
            dated_brackets_json = [
                dated_bracket_json
                for dated_bracket_json in (
                    generate_dated_bracket_json(bracket_json, instant_str)
                    for bracket_json in value
                    )
                if dated_bracket_json != dict()
                ]
            if not dated_brackets_json:
                return None
            dated_node_json[key] = dated_brackets_json
        elif key == 'values':
            # Occurs when @type == 'Parameter'.
            dated_value = generate_dated_json_value(value, instant_str)
            if dated_value is None:
                return None
            dated_node_json['value'] = dated_value
        else:
            dated_node_json[key] = value
    return dated_node_json


# Level-1 Converters


def validate_dated_legislation_json(dated_legislation_json, state = None):
    if dated_legislation_json is None:
        return None, None
    if state is None:
        state = conv.default_state

    dated_legislation_json, error = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            dict(
                instant = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.iso8601_input_to_date,
                    conv.date_to_iso8601_str,
                    conv.not_none,
                    ),
                ),
            constructor = dict,
            default = conv.noop,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(dated_legislation_json, state = state)
    if error is not None:
        return dated_legislation_json, error

    instant = dated_legislation_json.pop('instant')
    dated_legislation_json, error = validate_dated_node_json(dated_legislation_json, state = state)
    dated_legislation_json['instant'] = instant
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
                conv.test_equals(u'https://openfisca.fr/contexts/dated-legislation.jsonld'),
                ),
            '@type': conv.pipe(
                conv.test_isinstance(basestring),
                conv.cleanup_line,
                conv.test_in((u'Node', u'Parameter', u'Scale')),
                conv.not_none,
                ),
            'reference': conv.pipe(
                conv.test_isinstance(basestring),
                conv.cleanup_line,
                ),
            'description': conv.pipe(
                conv.test_isinstance(basestring),
                conv.cleanup_line,
                ),
            'end_line_number': conv.test_isinstance(int),
            'start_line_number': conv.test_isinstance(int),
            # baremes-ipp related attributes
            'conflicts': conv.pipe(
                conv.test_isinstance(list),
                conv.empty_to_none,
                conv.uniform_sequence(conv.test_isinstance(basestring)),
                ),
            'origin': conv.pipe(
                conv.test_isinstance(basestring),
                conv.empty_to_none,
                ),
            },
        constructor = dict,
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
        'description': conv.noop,
        'reference': conv.noop,
        'end_line_number': conv.test_isinstance(int),
        'start_line_number': conv.test_isinstance(int),
        # baremes-ipp related attributes
        'conflicts': conv.noop,
        'origin': conv.noop,
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
            brackets = conv.pipe(
                conv.test_isinstance(list),
                conv.uniform_sequence(
                    validate_dated_bracket_json,
                    drop_none_items = True,
                    ),
                validate_dated_brackets_json_types,
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
        constructor = dict,
        drop_none_values = 'missing',
        keep_value_order = True,
        )(validated_node, state = state)

    conv.remove_ancestor_from_state(state, node)
    return validated_node, errors


def validate_dated_bracket_json(bracket, state = None):
    if bracket is None:
        return None, None
    state = conv.add_ancestor_to_state(state, bracket)
    validated_bracket, errors = conv.pipe(
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
                reference = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_line,
                    ),
                end_line_number = conv.test_isinstance(int),
                rate = conv.item_or_sequence(
                    conv.pipe(
                        validate_dated_value_json,
                        conv.test_between(0, 1),
                        ),
                    ),
                start_line_number = conv.test_isinstance(int),
                threshold = conv.item_or_sequence(
                    conv.pipe(
                        validate_dated_value_json,
                        conv.test_greater_or_equal(0),
                        ),
                    ),
                ),
            constructor = dict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(bracket, state = state)
    conv.remove_ancestor_from_state(state, bracket)
    return validated_bracket, errors


def validate_dated_brackets_json_types(brackets, state = None):
    if not brackets:
        return brackets, None

    has_amount = any(
        'amount' in bracket
        for bracket in brackets
        )
    if has_amount:
        if state is None:
            state = conv.default_state
        errors = {}
        for bracket_index, bracket in enumerate(brackets):
            if 'base' in bracket:
                errors.setdefault(bracket_index, {})['base'] = state._(u"A scale can't contain both amounts and bases")
            if 'rate' in bracket:
                errors.setdefault(bracket_index, {})['rate'] = state._(u"A scale can't contain both amounts and rates")
        if errors:
            return brackets, errors
    return brackets, None


def validate_dated_value_json(value, state = None):
    if value is None:
        return None, None
    container = state.ancestors[-1]
    container_format = container.get('format')
    value_converters = dict(
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
        )
    value_converter = value_converters.get(container_format or 'float')  # Only parameters have a "format".
    assert value_converter is not None, 'Wrong format "{}", allowed: {}, container: {}'.format(
        container_format, value_converters.keys(), container)
    return value_converter(value, state = state or conv.default_state)


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
                conv.test_equals(u'https://openfisca.fr/contexts/legislation.jsonld'),
                ),
            '@type': conv.pipe(
                conv.test_isinstance(basestring),
                conv.cleanup_line,
                conv.test_in((u'Node', u'Parameter', u'Scale')),
                conv.not_none,
                ),
            'reference': conv.pipe(
                conv.test_isinstance(basestring),
                conv.cleanup_line,
                ),
            'description': conv.pipe(
                conv.test_isinstance(basestring),
                conv.cleanup_line,
                ),
            'end_line_number': conv.test_isinstance(int),
            'start_line_number': conv.test_isinstance(int),
            # baremes-ipp related attributes
            'conflicts': conv.pipe(
                conv.test_isinstance(list),
                conv.empty_to_none,
                conv.uniform_sequence(conv.test_isinstance(basestring)),
                ),
            'origin': conv.pipe(
                conv.test_isinstance(basestring),
                conv.empty_to_none,
                ),
            },
        constructor = dict,
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
        'reference': conv.noop,
        'description': conv.noop,
        'end_line_number': conv.noop,
        'start_line_number': conv.noop,
        # baremes-ipp related attributes
        'conflicts': conv.noop,
        'origin': conv.noop,
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
                conv.empty_to_none,
                conv.not_none,
                ),
            ))
    else:
        assert node_type == u'Scale'
        node_converters.update(dict(
            brackets = conv.pipe(
                conv.test_isinstance(list),
                conv.uniform_sequence(
                    validate_bracket_json,
                    drop_none_items = True,
                    ),
                validate_brackets_json_types,
                conv.empty_to_none,
                conv.not_none,
                ),
            option = conv.pipe(
                conv.test_isinstance(basestring),
                conv.input_to_slug,
                conv.test_in((
                    'contrib',
                    'main-d-oeuvre',
                    'noncontrib',
                    )),
                ),
            rates_kind = conv.pipe(
                conv.test_isinstance(basestring),
                conv.test_in((
                    'average',
                    )),
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
        constructor = dict,
        drop_none_values = 'missing',
        keep_value_order = True,
        )(validated_node, state = state)

    conv.remove_ancestor_from_state(state, node)
    return validated_node, errors


validate_legislation_json = validate_node_json


def validate_bracket_json(bracket, state = None):
    if bracket is None:
        return None, None
    state = conv.add_ancestor_to_state(state, bracket)
    validated_bracket, errors = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            dict(
                amount = validate_values_holder_json,
                base = validate_values_holder_json,
                reference = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_line,
                    ),
                end_line_number = conv.test_isinstance(int),
                rate = validate_values_holder_json,
                start_line_number = conv.test_isinstance(int),
                threshold = conv.pipe(
                    validate_values_holder_json,
                    conv.not_none,
                    ),
                ),
            constructor = dict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        conv.test(lambda bracket: bool(bracket.get('amount')) ^ bool(bracket.get('rate')),
            error = N_(u"Either amount or rate must be provided")),
        )(bracket, state = state)
    conv.remove_ancestor_from_state(state, bracket)
    return validated_bracket, errors


def validate_brackets_json_types(brackets, state = None):
    if not brackets:
        return brackets, None

    has_amount = any(
        'amount' in bracket
        for bracket in brackets
        )
    if has_amount:
        if state is None:
            state = conv.default_state
        errors = {}
        for bracket_index, bracket in enumerate(brackets):
            if 'base' in bracket:
                errors.setdefault(bracket_index, {})['base'] = state._(u"A scale can't contain both amounts and bases")
            if 'rate' in bracket:
                errors.setdefault(bracket_index, {})['rate'] = state._(u"A scale can't contain both amounts and rates")
        if errors:
            return brackets, errors
    return brackets, None


def validate_value_json(value, state = None):
    if value is None:
        return None, None
    container = state.ancestors[-1]
    container_format = container.get('format')
    value_converters = dict(
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
        )
    value_converter = value_converters.get(container_format or 'float')  # Only parameters have a "format".
    assert value_converter is not None, 'Wrong format "{}", allowed: {}, container: {}'.format(
        container_format, value_converters.keys(), container)
    state = conv.add_ancestor_to_state(state, value)
    validated_value, errors = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            {
                u'reference': conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_line,
                    ),
                u'end_line_number': conv.test_isinstance(int),
                u'start': conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.iso8601_input_to_date,
                    conv.date_to_iso8601_str,
                    conv.not_none,
                    ),
                u'start_line_number': conv.test_isinstance(int),
                u'value': conv.pipe(
                    value_converter,
                    ),
                },
            constructor = dict,
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
