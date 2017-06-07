# -*- coding: utf-8 -*-


"""Handle legislative parameters in XML format (and convert then to JSON)."""

import os

from lxml import etree


json_unit_by_xml_json_type = dict(
    age = u'year',
    days = u'day',
    hours = u'hour',
    monetary = u'currency',
    months = u'month',
    )


def load_xml_schema():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    filename_xml_schema = os.path.join(dir_path, 'legislation.xsd')

    with open(filename_xml_schema, 'r') as f:
        xmlschema_doc = etree.parse(f)
        xmlschema = etree.XMLSchema(xmlschema_doc)

    return xmlschema


def parse_and_validate_xml(xmlschema, legislation_xml_info_list):
    xml_trees = []
    for filename, path_in_legislation in legislation_xml_info_list:
        with open(filename, 'r') as f:
            tree = etree.parse(f)

        if not xmlschema.validate(tree):
            raise ValueError(xmlschema.error_log.filter_from_errors())

        xml_trees.append(tree)

    return xml_trees


def transform_values_history(children, value_format):
    value_list = []
    for child in children:
        if child.tag == 'VALUE':
            value = child.attrib['valeur']
            if value_format == bool:
                value = bool(int(value))
            else:
                value = float(value)
            value_list.append({
                'start': child.attrib['deb'],
                'value': value,
                })
        elif child.tag == 'END':
            value_list.append({
                'start': child.attrib['deb'],
                })

    value_list_sorted = sorted(value_list, key = lambda x: x['start'])[::-1]

    return value_list_sorted


def transform_etree_to_json_recursive(xml_node):
    json_node = dict()
    name = None
    value_format = None

    for key, value in xml_node.attrib.iteritems():
        if key == 'code':
            name = value
        elif key == 'format':
            if value == 'bool':
                json_node['format'] = 'boolean'
                value_format = bool
            elif value == 'percent':
                json_node['format'] = 'rate'
            else:
                json_node['format'] = value
        elif key == 'type':
            json_node['unit'] = json_unit_by_xml_json_type.get(value)
        elif key == 'conflicts':
            json_node['conflicts'] = value.split(',')
        elif key in {'description', 'origin', 'option', 'reference'}:
            json_node[key] = value
        else:
            raise ValueError(u'Unknown attribute "{}": "{}"'.format(key, value).encode('utf-8'))

    if xml_node.tag == 'NODE':
        json_node['@type'] = 'Node'

        children = dict()
        for child in xml_node:
            child_name, new_child = transform_etree_to_json_recursive(child)
            if child_name:
                children[child_name] = new_child
            else:
                assert new_child == {}  # comment
        json_node['children'] = children

    elif xml_node.tag == 'CODE':
        json_node['@type'] = 'Parameter'

        value_list = transform_values_history(xml_node, value_format)
        json_node['values'] = value_list

    elif xml_node.tag == 'BAREME':
        json_node['@type'] = 'Scale'

        brackets = []
        for child in xml_node:
            assert child.tag == 'TRANCHE'
            child_name, new_child = transform_etree_to_json_recursive(child)
            brackets.append(new_child)
        json_node['brackets'] = brackets

    elif xml_node.tag == 'TRANCHE':
        for child in xml_node:
            child_name, new_child = transform_etree_to_json_recursive(child)

            if child.tag == 'SEUIL':
                json_node['threshold'] = new_child
            elif child.tag == 'TAUX':
                json_node['rate'] = new_child
            elif child.tag == 'ASSIETTE':
                json_node['base'] = new_child
            elif child.tag == 'MONTANT':
                json_node['amount'] = new_child
            else:
                raise ValueError(u'Unknown TRANCHE child {}'.format(child.tag).encode('utf-8'))

    elif xml_node.tag == 'TAUX':
        json_node = transform_values_history(xml_node, value_format)

    elif xml_node.tag == 'SEUIL':
        json_node = transform_values_history(xml_node, value_format)

    elif xml_node.tag == 'ASSIETTE':
        json_node = transform_values_history(xml_node, value_format)

    elif xml_node.tag == 'MONTANT':
        json_node = transform_values_history(xml_node, value_format)

    elif xml_node.tag is etree.Comment:
        pass

    else:
        raise ValueError(u'Unknown tag {}'.format(xml_node.tag).encode('utf-8'))

    return name, json_node


def transform_etree_to_json_root(xml_trees):
    name_list = []
    json_list = []
    for tree in xml_trees:
        root = tree.getroot()
        name, json_data = transform_etree_to_json_recursive(root)
        name_list.append(name)
        json_list.append(json_data)
    return name_list, json_list


def merge(name_list, json_list, path_list):
    # The first json tree is special
    merged_json = json_list[0]
    assert not path_list[0]

    for name, json_tree, path in zip(name_list, json_list, path_list)[1:]:
        pointer = merged_json
        for key in path:
            if key in pointer['children']:
                pointer = pointer['children'][key]
            else:
                pointer['children'][key] = {
                    '@type': 'Node',
                    'children': {},
                    }

        assert name not in pointer['children'], u'{} is defined twice'.format('.'.join(path) + '.' + 'name').encode('utf-8')
        pointer['children'][name] = json_tree

    return merged_json


def load_legislation(legislation_xml_info_list):
    xmlschema = load_xml_schema()

    xml_trees = parse_and_validate_xml(xmlschema, legislation_xml_info_list)

    name_list, json_list = transform_etree_to_json_root(xml_trees)

    path_list = [path for filename, path in legislation_xml_info_list]
    merged_json = merge(name_list, json_list, path_list)

    return merged_json
