# -*- coding: utf-8 -*-


''' xml_to_yaml.py : Parse XML parameter files and convert them to YAML files

Comments are NOT converted.
'''
from __future__ import unicode_literals, print_function, division, absolute_import


import os
import re

from lxml import etree
import yaml

from openfisca_core.commons import to_unicode

node_keywords = ['reference', 'description']


def custom_str_representer(dumper, data):
    if re.match(r'^\d{4}-\d{2}-\d{2}$', data):
        tag = 'tag:yaml.org,2002:timestamp'
        return dumper.represent_scalar(tag, data)
    return dumper.represent_str(data)


def custom_unicode_representer(dumper, data):
    if re.match(r'^\d{4}-\d{2}-\d{2}$', data):
        tag = 'tag:yaml.org,2002:timestamp'
        return dumper.represent_scalar(tag, data)
    return dumper.represent_unicode(data)


yaml.add_representer(str, custom_str_representer, Dumper=yaml.SafeDumper)
yaml.add_representer(to_unicode, custom_unicode_representer, Dumper=yaml.SafeDumper)


# Load

def load_xml_schema():
    dir_path = os.path.dirname(__file__)
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
    values = {}
    for child in children:
        if child.tag == etree.Comment:
            print('Warning : ignoring comment "{}"'.format(child))
            continue

        date = child.attrib['deb']
        assert date not in values

        if child.tag == 'VALUE':
            value = child.attrib['valeur']
            if value_format == bool:
                value = bool(int(value))
            else:
                value = float(value)
            values[date] = {'value': value}
        elif child.tag == 'END':
            values[date] = {'value': None}
        elif child.tag == 'PLACEHOLDER':
            values[date] = 'expected'

        if 'reference' in child.attrib:
            if values[date] == 'expected':
                values[date] = {'expected': None, 'reference': child.attrib['reference']}
            else:
                values[date]['reference'] = child.attrib['reference']

    return values


def transform_etree_to_json_recursive(xml_node):
    json_node = dict()
    name = None
    value_format = None

    for key, value in xml_node.attrib.items():
        if key == 'code':
            name = value
        elif key == 'format':
            if value == 'percent':
                if 'unit' not in json_node:
                    json_node['unit'] = '/1'
                else:
                    del json_node['unit']
        elif key == 'type':
            if value == 'age':
                if 'unit' not in json_node:
                    json_node['unit'] = 'year'
                else:
                    del json_node['unit']
            elif value == 'monetary':
                if 'unit' not in json_node:
                    json_node['unit'] = 'currency'
                else:
                    del json_node['unit']
        elif key in {'conflicts', 'option'}:
            pass
        elif key == 'origin':
            if 'reference' not in json_node:
                json_node['reference'] = value
        elif key in {'description', 'reference'}:
            json_node[key] = to_unicode(value)
        else:
            raise ValueError('Unknown attribute "{}": "{}"'.format(key, value).encode('utf-8'))

    if xml_node.tag == 'NODE':
        json_node['type'] = 'node'

        for child in xml_node:
            child_name, new_child = transform_etree_to_json_recursive(child)
            if child_name:
                json_node[child_name] = new_child
            else:
                assert new_child == {}  # comment

    elif xml_node.tag == 'CODE':
        json_node['type'] = 'parameter'

        value_list = transform_values_history(xml_node, value_format)
        json_node['values'] = value_list

    elif xml_node.tag == 'BAREME':
        json_node['type'] = 'scale'

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
                raise ValueError('Unknown TRANCHE child {}'.format(child.tag).encode('utf-8'))

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
        raise ValueError('Unknown tag {}'.format(xml_node.tag).encode('utf-8'))

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


# Merge

def merge(name_list, json_list, path_list):
    merged_json = {'type': 'node'}

    for name, json_tree, path in zip(name_list, json_list, path_list):
        pointer = merged_json
        for key in path:
            if key in pointer:
                pointer = pointer[key]
            else:
                pointer[key] = {
                    'type': 'node',
                    }

        assert name not in pointer, '{} is defined twice'.format('.'.join(path) + '.' + 'name').encode('utf-8')
        pointer[name] = json_tree

    return merged_json


def load_legislation(legislation_xml_info_list):
    xmlschema = load_xml_schema()

    xml_trees = parse_and_validate_xml(xmlschema, legislation_xml_info_list)

    name_list, json_list = transform_etree_to_json_root(xml_trees)

    path_list = [path for filename, path in legislation_xml_info_list]
    merged_json = merge(name_list, json_list, path_list)

    return merged_json


# Write YAML

def write_yaml(node, path):
    node_type = node['type']
    del node['type']

    if node_type == 'node':
        os.mkdir(path)
        metadata = {k: node[k] for k in node_keywords if k in node}
        children = {k: node[k] for k in node if k not in node_keywords}

        if metadata:
            yaml_filename = os.path.join(path, 'index.yaml')
            with open(yaml_filename, 'w') as f:
                yaml.safe_dump(metadata, f, default_flow_style=False, allow_unicode=True)

        for child_name, child in children.items():
            write_yaml(child, os.path.join(path, child_name))

    elif node_type == 'parameter':
        yaml_filename = path + '.yaml'
        with open(yaml_filename, 'w') as f:
            yaml.safe_dump(node, f, default_flow_style=False, allow_unicode=True)

    elif node_type == 'scale':
        yaml_filename = path + '.yaml'
        with open(yaml_filename, 'w') as f:
            yaml.safe_dump(node, f, default_flow_style=False, allow_unicode=True)

    else:
        raise ValueError('Unknown type {}'.format(node_type))


def write_parameters(legislation_xml_info_list, path):
    params_tree = load_legislation(legislation_xml_info_list)

    write_yaml(params_tree, path)
