# -*- coding: utf-8 -*-

''' xml_to_json.py : Parse XML parameter files and convert them to YAML files
'''

import os

import yaml

import legislationsxml


def parse_values_history(values_input):
    values = {}
    for value_input in values_input:
        assert set(value_input.keys()).issubset(set(['value', 'start'])), value_input
        date = value_input['start']
        assert date not in values
        if 'value' in value_input:
            values[date] = {'value': value_input['value']}
        else:
            values[date] = {}
    return values


def convert_node(node, path):
    node_data = {}

    node_type = node['@type']
    if node_type == 'Node':
        os.mkdir(path)

        for k, v in node.items():
            if k == '@type':
                pass
            elif k == 'description':
                node_data['description'] = v
            elif k == 'reference':
                node_data['reference'] = v
            elif k == 'origin':
                if 'reference' not in node_data:
                    node_data['reference'] = v
            elif k == 'children':
                for name, child in v.items():
                    child_path = os.path.join(path, name)
                    convert_node(child, child_path)
            else:
                raise ValueError('Unknown key {}'.format((k, v)))

        yaml_filename = os.path.join(path, '_.yaml')
        with open(yaml_filename, 'w') as f:
            yaml.dump(node_data, f, default_flow_style=False)

    elif node_type == 'Parameter':
        for k, v in node.items():
            if k == '@type':
                node_data['type'] = 'parameter'
            elif k == 'description':
                node_data['description'] = v
            elif k == 'format':
                assert 'unit' not in node_data
                if v == 'rate':
                    node_data['unit'] = '/1'
            elif k == 'unit':
                assert 'unit' not in node_data
                if v == 'currency':
                    node_data['unit'] = 'currency'
                elif v == 'year':
                    node_data['unit'] = 'year'
            elif k == 'reference':
                node_data['reference'] = v
            elif k == 'origin':
                if 'reference' not in node_data:
                    node_data['reference'] = v
            elif k == 'values':
                node_data['values'] = parse_values_history(v)
            elif k == 'conflicts':
                pass
            else:
                raise ValueError('Unknown key {}'.format((k, v)))

            yaml_filename = path + '.yaml'
            with open(yaml_filename, 'w') as f:
                yaml.dump(node_data, f, default_flow_style=False)

    elif node_type == 'Scale':
        for k, v in node.items():
            if k == '@type':
                node_data['type'] = 'scale'
            elif k == 'description':
                node_data['description'] = v
            elif k == 'option':
                node_data['option'] = v
            elif k == 'reference':
                node_data['reference'] = v
            elif k == 'origin':
                if 'reference' not in node_data:
                    node_data['reference'] = v
            elif k == 'unit':
                node_data['unit'] = v
            elif k == 'conflicts':
                pass
            elif k == 'brackets':
                brackets = []
                for bracket_input in v:
                    bracket_data = {}
                    for bracket_key, bracket_value in bracket_input.items():
                        if bracket_key == 'origin':
                            if 'reference' not in bracket_data:
                                bracket_data['reference'] = bracket_value
                        elif bracket_key == 'threshold':
                            bracket_data['threshold'] = parse_values_history(bracket_value)
                        elif bracket_key == 'rate':
                            bracket_data['rate'] = parse_values_history(bracket_value)
                        elif bracket_key == 'amount':
                            bracket_data['amount'] = parse_values_history(bracket_value)
                        elif bracket_key == 'base':
                            bracket_data['base'] = parse_values_history(bracket_value)
                        else:
                            raise ValueError('Unknown key {}'.format((bracket_key, bracket_value)))

                    brackets.append(bracket_data)
                node_data['brackets'] = brackets

            else:
                raise ValueError('Unknown key {}'.format((k, v)))

            yaml_filename = path + '.yaml'
            with open(yaml_filename, 'w') as f:
                yaml.dump(node_data, f, default_flow_style=False)

    else:
        raise ValueError('Unknown @type {}'.format(node_type))


def convert_files(legislation_xml_info_list, path):
    params_tree = legislationsxml.load_legislation(legislation_xml_info_list)

    convert_node(params_tree, path)
