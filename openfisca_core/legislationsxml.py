# -*- coding: utf-8 -*-


"""Handle legislative parameters in XML format (and convert then to JSON)."""


import collections
import logging
import itertools

import xml.etree.ElementTree

from . import conv


# legislation_json_key_by_xml_tag = dict(
#    ASSIETTE = 'base',  # "base" is singular, because a bracket has only one base.
#    BAREME = 'scales',
#    CODE = 'parameters',
#    MONTANT = 'amount',
#    NODE = 'nodes',
#    SEUIL= 'threshold',  # "threshold" is singular, because a bracket has only one base.
#    TAUX = 'rate',  # "rate" is singular, because a bracket has only one base.
#    TRANCHE = 'brackets', # TODO: should be renamed to bracket
#    VALUE = 'values',
#    END
#    PLACEHOLDER
#    )

default_format = 'float'
log = logging.getLogger(__name__)
json_unit_by_xml_json_type = dict(
    age = u'year',
    days = u'day',
    hours = u'hour',
    monetary = u'currency',
    months = u'month',
    )
xml_json_formats = (
    'bool',
    'float',
    'integer',
    'percent',
    )


# Helper functions

def N_(message):
    return message


# Level 1 converters


def merge_xml_elements_and_paths_into_first(xml_elements_and_paths, state = None):
    """
    This converter merges multiple XML elements into the first.

    Warning: it mutates the first XML element of `xml_elements`.
    """
    if xml_elements_and_paths is None:
        return xml_elements_and_paths, None
    xml_root_element = xml_elements_and_paths[0][0]
    for xml_element, path in xml_elements_and_paths[1:]:
        if path is None:
            xml_root_element.append(xml_element)
        else:
            xpath = u'/'.join(itertools.chain(
                    [u'.'],
                (u'NODE[@code="{}"]'.format(fragment) for fragment in path)
                ))
            xml_root_element.find(xpath).append(xml_element)

    return xml_root_element, None


def translate_xml_element_to_json_item(xml_element):
    json_element = collections.OrderedDict()
    text = xml_element.text
    if text is not None:
        text = text.strip().strip('#').strip() or None
        if text is not None:
            json_element['text'] = text
    xml_file_path = getattr(xml_element, "xml_file_path", None)
    if xml_file_path is not None:
        json_element['xml_file_path'] = xml_file_path
    start_line_number = getattr(xml_element, "start_line_number", None)
    if start_line_number is not None:
        json_element['start_line_number'] = start_line_number
    end_line_number = getattr(xml_element, "end_line_number", None)
    if end_line_number is not None and end_line_number != start_line_number:
        json_element['end_line_number'] = end_line_number
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


def transform_bracket_xml_json_to_json(bracket_xml_json):
    comments = []
    bracket_json = collections.OrderedDict()
    for key, value in bracket_xml_json.iteritems():
        if key == 'ASSIETTE':
            bracket_json['base'] = transform_values_holder_xml_json_to_json(value[0])
        elif key == 'code':
            pass
        elif key == 'MONTANT':
            bracket_json['amount'] = transform_values_holder_xml_json_to_json(value[0])
        elif key == 'SEUIL':
            bracket_json['threshold'] = transform_values_holder_xml_json_to_json(value[0])
        elif key in ('tail', 'text'):
            comments.append(value)
        elif key == 'TAUX':
            bracket_json['rate'] = transform_values_holder_xml_json_to_json(value[0])

        else:
            bracket_json[key] = value
    if comments:
        bracket_json['comment'] = u'\n\n'.join(comments)
    return bracket_json


def transform_node_xml_json_to_json(node_xml_json, root = True):
    comments = []
    node_json = collections.OrderedDict()
    if root:
        node_json['@context'] = u'http://openfisca.fr/contexts/legislation.jsonld'
    node_json['@type'] = 'Node'
    child_json_by_code = {}
    for key, value in node_xml_json.iteritems():
        if key == 'BAREME':
            for child_xml_json in value:
                child_code, child_json = transform_scale_xml_json_to_json(child_xml_json)
                child_json_by_code[child_code] = child_json
        elif key == 'CODE':
            for child_xml_json in value:
                child_code, child_json = transform_parameter_xml_json_to_json(child_xml_json)
                child_json_by_code[child_code] = child_json
        elif key == 'code':
            pass
        elif key == 'deb':
            node_json['start'] = value
        elif key == 'fin':
            node_json['stop'] = value
        elif key == 'NODE':
            for child_xml_json in value:
                child_code, child_json = transform_node_xml_json_to_json(child_xml_json, root = False)
                child_json_by_code[child_code] = child_json
        elif key in ('tail', 'text'):
            comments.append(value)
        else:
            node_json[key] = value
    node_json['children'] = collections.OrderedDict(sorted(child_json_by_code.iteritems()))
    if comments:
        node_json['comment'] = u'\n\n'.join(comments)
    return node_xml_json['code'], node_json


def transform_parameter_xml_json_to_json(parameter_xml_json):
    comments = []
    parameter_json = collections.OrderedDict()
    parameter_json['@type'] = 'Parameter'
    xml_json_value_to_json_transformer = float

    def xml_json_value_to_json_transformer_bool(xml_json_value):
        return bool(int(xml_json_value))

    if 'description' in parameter_xml_json:
        parameter_json['description'] = parameter_xml_json['description']

    if 'format' in parameter_xml_json:
        value = parameter_xml_json['format']
        parameter_json['format'] = dict(
            bool = u'boolean',
            percent = u'rate',
            ).get(value, value)
        if value == 'bool':
            xml_json_value_to_json_transformer = xml_json_value_to_json_transformer_bool
        elif value == 'integer':
            xml_json_value_to_json_transformer = int

    if 'tail' in parameter_xml_json:
        comments.append(parameter_xml_json['tail'])

    if 'text' in parameter_xml_json:
        comments.append(parameter_xml_json['text'])

    if 'type' in parameter_xml_json:
        value = parameter_xml_json['type']
        parameter_json['unit'] = json_unit_by_xml_json_type.get(value, value)

    values = [
        transform_value_xml_json_to_json(item, xml_json_value_to_json_transformer)
        for item in parameter_xml_json['VALUE']
        ]

    if 'END' in parameter_xml_json:
        ends = [
            transform_end_xml_json_to_json(item)
            for item in parameter_xml_json['END']
            ]
    else:
        ends = []

    # Sort by "deb" date
    sorted_values_json = sorted(values + ends, key = lambda value_xml_json: value_xml_json['start'], reverse = True)
    parameter_json['values'] = sorted_values_json

    if parameter_json.get('format') is None:
        parameter_json['format'] = default_format
    if comments:
        parameter_json['comment'] = u'\n\n'.join(comments)
    return parameter_xml_json['code'], parameter_json


def transform_scale_xml_json_to_json(scale_xml_json):
    comments = []
    scale_json = collections.OrderedDict()
    scale_json['@type'] = 'Scale'
    for key, value in scale_xml_json.iteritems():
        if key == 'code':
            pass
        elif key in ('tail', 'text'):
            comments.append(value)
        elif key == 'TRANCHE':
            scale_json['brackets'] = [
                transform_bracket_xml_json_to_json(item)
                for item in value
                ]
        elif key == 'type':
            scale_json['unit'] = json_unit_by_xml_json_type.get(value, value)
        else:
            scale_json[key] = value
    if comments:
        scale_json['comment'] = u'\n\n'.join(comments)
    return scale_xml_json['code'], scale_json


def transform_value_xml_json_to_json(value_xml_json, xml_json_value_to_json_transformer):
    comments = []
    value_json = collections.OrderedDict()
    for key, value in value_xml_json.iteritems():
        assert key not in ('code', 'format', 'type')
        if key == 'deb':
            value_json['start'] = value
        elif key in ('tail', 'text'):
            comments.append(value)
        elif key == 'valeur':
            try:
                value_json['value'] = xml_json_value_to_json_transformer(value)
            except TypeError:
                log.error(u'Invalid value: {}'.format(value))
                raise
        else:
            value_json[key] = value
    if comments:
        value_json['comment'] = u'\n\n'.join(comments)
    return value_json


def transform_end_xml_json_to_json(end_xml_json):
    comments = []
    end_json = collections.OrderedDict()
    for key, value in end_xml_json.iteritems():
        assert key not in ('code', 'format', 'type')
        if key == 'deb':
            end_json['start'] = value
        elif key in ('tail', 'text'):
            comments.append(value)
        else:
            end_json[key] = value
    if comments:
        end_json['comment'] = u'\n\n'.join(comments)
    return end_json


def transform_values_holder_xml_json_to_json(values_holder_xml_json):
    values = [
        transform_value_xml_json_to_json(item, float)
        for item in values_holder_xml_json['VALUE']
        ]

    if 'END' in values_holder_xml_json:
        ends = [
            transform_end_xml_json_to_json(item)
            for item in values_holder_xml_json['END']
            ]
    else:
        ends = []

    # Sort by "deb" date
    sorted_values_json = sorted(values + ends, key = lambda value_xml_json: value_xml_json['start'], reverse = True)

    return sorted_values_json


def validate_bracket_xml_json(bracket, state = None):
    if bracket is None:
        return None, None
    state = conv.add_ancestor_to_state(state, bracket)
    validated_bracket, errors = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            dict(
                ASSIETTE = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        validate_values_holder_xml_json,
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    conv.test(lambda l: len(l) == 1, error = N_(u"List must contain one and only one item")),
                    ),
                code = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_line,
                    ),
                end_line_number = conv.test_isinstance(int),
                MONTANT = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        validate_values_holder_xml_json,
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    conv.test(lambda l: len(l) == 1, error = N_(u"List must contain one and only one item")),
                    ),
                SEUIL = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        validate_values_holder_xml_json,
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    conv.test(
                        lambda l: len(l) == 1, error = N_(u"List must contain one and only one item")),
                    conv.not_none,
                    ),
                start_line_number = conv.test_isinstance(int),
                tail = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                TAUX = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        validate_values_holder_xml_json,
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    conv.test(lambda l: len(l) == 1, error = N_(u"List must contain one and only one item")),
                    ),
                text = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                # baremes-ipp related attributes
                origin = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.empty_to_none,
                    ),
                ),
            constructor = collections.OrderedDict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        conv.test(lambda bracket: bool(bracket.get('MONTANT')) ^ bool(bracket.get('TAUX')),
            error = N_(u"Either MONTANT or TAUX must be provided")),
        )(bracket, state = state)
    conv.remove_ancestor_from_state(state, bracket)
    return validated_bracket, errors


def validate_brackets_xml_json_types(brackets, state = None):
    if not brackets:
        return brackets, None

    has_amount = any(
        'MONTANT' in bracket
        for bracket in brackets
        )
    if has_amount:
        if state is None:
            state = conv.default_state
        errors = {}
        for bracket_index, bracket in enumerate(brackets):
            if 'ASSIETTE' in bracket:
                errors.setdefault(bracket_index, {})['ASSIETTE'] = state._(
                    u"A scale can't contain both MONTANT and ASSIETTE")
            if 'TAUX' in bracket:
                errors.setdefault(bracket_index, {})['TAUX'] = state._(u"A scale can't contain both MONTANT and TAUX")
        if errors:
            return brackets, errors
    return brackets, None


def validate_node_xml_json(node, state = None):
    if node is None:
        return None, None
    state = conv.add_ancestor_to_state(state, node)
    validated_node, errors = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            dict(
                BAREME = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        validate_scale_xml_json,
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    ),
                CODE = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        validate_parameter_xml_json,
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    ),
                code = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_line,
                    conv.not_none,
                    ),
                description = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_line,
                    ),
                end_line_number = conv.test_isinstance(int),
                NODE = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        validate_node_xml_json,
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    ),
                start_line_number = conv.test_isinstance(int),
                tail = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                text = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                xml_file_path = conv.test_isinstance(basestring),
                # baremes-ipp related attributes
                conflicts = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.empty_to_none,
                    conv.function(lambda value: value.split(',')),
                    ),
                origin = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.empty_to_none,
                    ),
                ),
            constructor = collections.OrderedDict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(node, state = state)
    if errors is None:
        children_groups_key = ('BAREME', 'CODE', 'NODE')
        if all(
                validated_node.get(key) is None
                for key in children_groups_key
                ):
            error = state._(u"At least one of the following items must be present: {}").format(state._(u', ').join(
                u'"{}"'.format(key)
                for key in children_groups_key
                ))
            errors = dict(
                (key, error)
                for key in children_groups_key
                )
        else:
            errors = {}
        children_code = set()
        for key in children_groups_key:
            for child_index, child in enumerate(validated_node.get(key) or []):
                child_code = child['code']
                if child_code in children_code:
                    errors.setdefault(key, {}).setdefault(child_index, {})['code'] = state._(u"Duplicate value")
                else:
                    children_code.add(child_code)
    conv.remove_ancestor_from_state(state, node)
    return validated_node, errors or None


validate_legislation_xml_json = validate_node_xml_json


def validate_parameter_xml_json(parameter, state = None):
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
                description = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_line,
                    ),
                end_line_number = conv.test_isinstance(int),
                format = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.input_to_slug,
                    conv.test_in(xml_json_formats),
                    ),
                start_line_number = conv.test_isinstance(int),
                tail = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                taille = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.test_in([
                        'moinsde20',
                        'plusde20',
                        ]),
                    ),
                text = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                type = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.input_to_slug,
                    conv.test_in(json_unit_by_xml_json_type),
                    ),
                VALUE = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        validate_value_xml_json,
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    conv.not_none,
                    ),
                END = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        validate_end_xml_json,
                        drop_none_items = True,
                        ),
                    ),
                PLACEHOLDER = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        validate_placeholder_xml_json,
                        drop_none_items = True,
                        ),
                    ),
                xml_file_path = conv.test_isinstance(basestring),
                # baremes-ipp related attributes
                conflicts = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.empty_to_none,
                    conv.function(lambda value: value.split(',')),
                    ),
                origin = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.empty_to_none,
                    ),
                ),
            constructor = collections.OrderedDict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(parameter, state = state)
    conv.remove_ancestor_from_state(state, parameter)
    return validated_parameter, errors


def validate_scale_xml_json(scale, state = None):
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
                description = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_line,
                    ),
                end_line_number = conv.test_isinstance(int),
                option = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.input_to_slug,
                    conv.test_in((
                        'contrib',
                        'main-d-oeuvre',
                        'noncontrib',
                        )),
                    ),
                start_line_number = conv.test_isinstance(int),
                TRANCHE = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        validate_bracket_xml_json,
                        drop_none_items = True,
                        ),
                    validate_brackets_xml_json_types,
                    conv.empty_to_none,
                    conv.not_none,
                    ),
                tail = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                text = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                type = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.input_to_slug,
                    conv.test_in((
                        'monetary',
                        )),
                    ),
                xml_file_path = conv.test_isinstance(basestring),
                # baremes-ipp related attributes
                conflicts = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.empty_to_none,
                    conv.function(lambda value: value.split(',')),
                    ),
                origin = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.empty_to_none,
                    ),
                ),
            constructor = collections.OrderedDict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(scale, state = state)
    conv.remove_ancestor_from_state(state, scale)
    return validated_scale, errors


def validate_value_xml_json(value, state = None):
    if value is None:
        return None, None
    container = state.ancestors[-1]
    value_converter = dict(
        bool = conv.pipe(
            conv.test_isinstance(basestring),
            conv.cleanup_line,
            conv.test_in([u'0', u'1']),
            ),
        float = conv.pipe(
            conv.test_isinstance(basestring),
            conv.cleanup_line,
            conv.test_conv(conv.anything_to_float),
            ),
        integer = conv.pipe(
            conv.test_isinstance(basestring),
            conv.cleanup_line,
            conv.test_conv(conv.anything_to_strict_int),
            ),
        percent = conv.pipe(
            conv.test_isinstance(basestring),
            conv.cleanup_line,
            conv.test_conv(conv.anything_to_float),
            ),
        )[container.get('format') or default_format]  # Only CODE have a "format".
    state = conv.add_ancestor_to_state(state, value)
    validated_value, errors = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            dict(
                deb = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.iso8601_input_to_date,
                    conv.date_to_iso8601_str,
                    conv.not_none,
                    ),
                end_line_number = conv.test_isinstance(int),
                start_line_number = conv.test_isinstance(int),
                tail = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                text = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                valeur = conv.pipe(
                    value_converter,
                    conv.not_none,
                    ),
                xml_file_path = conv.test_isinstance(basestring),
                # baremes-ipp related attributes
                origin = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.empty_to_none,
                    ),
                ),
            constructor = collections.OrderedDict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(value, state = state)
    conv.remove_ancestor_from_state(state, value)
    return validated_value, errors


def validate_end_xml_json(value, state = None):
    if value is None:
        return None, None
    state = conv.add_ancestor_to_state(state, value)
    validated_value, errors = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            dict(
                deb = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.iso8601_input_to_date,
                    conv.date_to_iso8601_str,
                    conv.not_none,
                    ),
                end_line_number = conv.test_isinstance(int),
                start_line_number = conv.test_isinstance(int),
                tail = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                text = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                xml_file_path = conv.test_isinstance(basestring),
                # baremes-ipp related attributes
                origin = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.empty_to_none,
                    ),
                ),
            constructor = collections.OrderedDict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(value, state = state)
    conv.remove_ancestor_from_state(state, value)
    return validated_value, errors


def validate_placeholder_xml_json(value, state = None):
    if value is None:
        return None, None
    state = conv.add_ancestor_to_state(state, value)
    validated_value, errors = conv.pipe(
        conv.test_isinstance(dict),
        conv.struct(
            dict(
                deb = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.iso8601_input_to_date,
                    conv.date_to_iso8601_str,
                    conv.not_none,
                    ),
                end_line_number = conv.test_isinstance(int),
                start_line_number = conv.test_isinstance(int),
                tail = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                text = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.cleanup_text,
                    ),
                xml_file_path = conv.test_isinstance(basestring),
                # baremes-ipp related attributes
                origin = conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.empty_to_none,
                    ),
                ),
            constructor = collections.OrderedDict,
            drop_none_values = 'missing',
            keep_value_order = True,
            ),
        )(value, state = state)
    conv.remove_ancestor_from_state(state, value)
    return validated_value, errors


validate_values_holder_xml_json = conv.struct(
    dict(
        end_line_number = conv.test_isinstance(int),
        start_line_number = conv.test_isinstance(int),
        VALUE = conv.pipe(
            conv.test_isinstance(list),
            conv.uniform_sequence(
                validate_value_xml_json,
                drop_none_items = True,
                ),
            conv.empty_to_none,
            conv.not_none,
            ),
        END = conv.pipe(
            conv.test_isinstance(list),
            conv.uniform_sequence(
                validate_end_xml_json,
                drop_none_items = True,
                ),
            ),
        PLACEHOLDER = conv.pipe(
            conv.test_isinstance(list),
            conv.uniform_sequence(
                validate_placeholder_xml_json,
                drop_none_items = True,
                ),
            ),
        xml_file_path = conv.test_isinstance(basestring),
        # baremes-ipp related attributes
        conflicts = conv.pipe(
            conv.test_isinstance(basestring),
            conv.empty_to_none,
            conv.function(lambda value: value.split(',')),
            ),
        origin = conv.pipe(
            conv.test_isinstance(basestring),
            conv.empty_to_none,
            ),
        ),
    constructor = collections.OrderedDict,
    drop_none_values = 'missing',
    keep_value_order = True,
    )


def make_xml_legislation_file_path_to_xml(with_source_file_infos = False):
    def xml_legislation_file_path_to_xml(value, state = None):
        if with_source_file_infos:
            # From # http://bugs.python.org/issue14078#msg153907
            class XMLParserWithLineNumbers(xml.etree.ElementTree.XMLParser):
                def _end(self, *args, **kwargs):
                    element = super(self.__class__, self)._end(*args, **kwargs)
                    element.end_line_number = self._parser.CurrentLineNumber
                    return element

                def _start_list(self, *args, **kwargs):
                    element = super(self.__class__, self)._start_list(*args, **kwargs)
                    element.start_line_number = self._parser.CurrentLineNumber
                    tag_name = args[0]
                    if tag_name in ('BAREME', 'CODE', 'NODE'):
                        element.xml_file_path = value
                    return element

            parser = XMLParserWithLineNumbers()
        else:
            parser = None
        try:
            legislation_tree = xml.etree.ElementTree.parse(value, parser = parser)
        except xml.etree.ElementTree.ParseError as error:
            return value, unicode(error)
        xml_legislation = legislation_tree.getroot()
        return xml_legislation, None

    return xml_legislation_file_path_to_xml


def make_xml_legislation_info_list_to_xml_elements_and_paths(with_source_file_infos):
    return conv.uniform_sequence(
        conv.struct([
            make_xml_legislation_file_path_to_xml(with_source_file_infos),
            conv.pipe(
                conv.test_isinstance((list, tuple)),
                conv.uniform_sequence(conv.test_isinstance(basestring)),
                ),
            ]),
        )


def xml_legislation_to_json(xml_element, state = None):
    if xml_element is None:
        return None, None
    json_key, json_element = translate_xml_element_to_json_item(xml_element)
    if json_key != 'NODE':
        if state is None:
            state = conv.default_state
        return json_element, state._(u'Invalid root element in XML: "{}" instead of "NODE"').format(xml_element.tag)
    return json_element, None


# Level 2 converters

def make_xml_legislation_info_list_to_xml_element(with_source_file_infos):
    return conv.pipe(
        make_xml_legislation_info_list_to_xml_elements_and_paths(with_source_file_infos),
        merge_xml_elements_and_paths_into_first,
        )


# Used by taxbenefitsystems.MultipleXmlBasedTaxBenefitSystem

def make_xml_legislation_info_list_to_json(with_source_file_infos):
    return conv.pipe(
        make_xml_legislation_info_list_to_xml_element(with_source_file_infos),
        xml_legislation_to_json,
        validate_legislation_xml_json,
        conv.function(lambda value: transform_node_xml_json_to_json(value)[1]),
        )
