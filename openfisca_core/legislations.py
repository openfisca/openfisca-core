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
        message = u"The parameter '{}'".format(name)
        if variable_name is not None:
            message += u" requested by variable '{}'".format(variable_name)
        message += (
            u" was not found in the {2} tax and benefit system."
            ).format(name, variable_name, instant)
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
