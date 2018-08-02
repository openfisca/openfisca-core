# -*- coding: utf-8 -*-


"""Handle decompositions in XML format (and convert then to JSON)."""

from __future__ import unicode_literals, print_function, division, absolute_import
import collections

from openfisca_core import conv
from openfisca_core.commons import basestring_type, to_unicode


def N_(message):
    return message


def transform_node_xml_json_to_json(node_xml_json, root = True):
    comments = []
    node_json = collections.OrderedDict()
    if root:
        node_json['@context'] = 'https://openfisca.fr/contexts/decomposition.jsonld'
    node_json['@type'] = 'Node'
    children_json = []
    for key, value in node_xml_json.items():
        if key == 'color':
            node_json['color'] = [
                int(color)
                for color in value.split(',')
                ]
        elif key == 'desc':
            node_json['name'] = value
        elif key == 'shortname':
            node_json['short_name'] = value
        elif key == 'NODE':
            for child_xml_json in value:
                children_json.append(transform_node_xml_json_to_json(child_xml_json, root = False))
        elif key in ('tail', 'text'):
            comments.append(value)
        elif key == 'typevar':
            node_json['type'] = value
        else:
            node_json[key] = value
    if children_json:
        node_json['children'] = children_json
    if comments:
        node_json['comment'] = '\n\n'.join(comments)
    return node_json


def translate_xml_element_to_json_item(xml_element):
    json_element = collections.OrderedDict()
    text = xml_element.text
    if text is not None:
        text = text.strip().strip('#').strip() or None
        if text is not None:
            json_element['text'] = text
    json_element.update(xml_element.attrib)
    for xml_child in xml_element:
        json_child_key, json_child = translate_xml_element_to_json_item(xml_child)
        json_element.setdefault(json_child_key, []).append(json_child)
    tail = xml_element.tail
    if tail is not None:
        tail = tail.strip().strip('#').strip() or None
        if tail is not None:
            json_element['tail'] = tail
    return xml_element.tag, json_element


def make_validate_node_xml_json(tax_benefit_system):
    def validate_node_xml_json(node, state = None):
        validated_node, errors = conv.pipe(
            conv.test_isinstance(dict),
            conv.struct(
                dict(
                    code = conv.pipe(
                        conv.test_isinstance(basestring_type),
                        conv.cleanup_line,
                        conv.not_none,
                        ),
                    color = conv.pipe(
                        conv.test_isinstance(basestring_type),
                        conv.function(lambda colors: colors.split(',')),
                        conv.uniform_sequence(
                            conv.pipe(
                                conv.input_to_int,
                                conv.test_between(0, 255),
                                conv.not_none,
                                ),
                            ),
                        conv.test(lambda colors: len(colors) == 3, error = N_('Wrong number of colors in triplet.')),
                        conv.function(lambda colors: ','.join(to_unicode(color) for color in colors)),
                        ),
                    desc = conv.pipe(
                        conv.test_isinstance(basestring_type),
                        conv.cleanup_line,
                        conv.not_none,
                        ),
                    NODE = conv.pipe(
                        conv.test_isinstance(list),
                        conv.uniform_sequence(
                            validate_node_xml_json,
                            drop_none_items = True,
                            ),
                        conv.empty_to_none,
                        ),
                    shortname = conv.pipe(
                        conv.test_isinstance(basestring_type),
                        conv.cleanup_line,
                        conv.not_none,
                        ),
                    tail = conv.pipe(
                        conv.test_isinstance(basestring_type),
                        conv.cleanup_text,
                        ),
                    text = conv.pipe(
                        conv.test_isinstance(basestring_type),
                        conv.cleanup_text,
                        ),
                    typevar = conv.pipe(
                        conv.test_isinstance(basestring_type),
                        conv.input_to_int,
                        conv.test_equals(2),
                        ),
                    ),
                constructor = collections.OrderedDict,
                drop_none_values = 'missing',
                keep_value_order = True,
                ),
            )(node, state = state or conv.default_state)
        if errors is not None:
            return validated_node, errors

        if not validated_node.get('NODE'):
            validated_node, errors = conv.struct(
                dict(
                    code = conv.test_in(tax_benefit_system.variables),
                    ),
                default = conv.noop,
                )(validated_node, state = state)
        return validated_node, errors

    return validate_node_xml_json


def xml_decomposition_to_json(xml_element, state = None):
    if xml_element is None:
        return None, None
    json_key, json_element = translate_xml_element_to_json_item(xml_element)
    if json_key != 'NODE':
        if state is None:
            state = conv.default_state
        return json_element, state._('Invalid root element in XML: "{}" instead of "NODE"').format(xml_element.tag)
    return json_element, None
