# -*- coding: utf-8 -*-

"""Handle legislative parameters in YAML format"""

import os

import yaml


def parse_dir(path):
    node_data = {'type': 'node', 'children': {}}

    for child_name in os.listdir(path):
        child_path = os.path.join(path, child_name)
        if os.path.isfile(child_path):
            child_name, ext = os.path.splitext(child_name)
            assert ext == '.yaml'
            with open(child_path, 'r') as f:
                data = yaml.load(f)

            if child_name == '_':
                node_data.update(data)
            else:
                if data['type'] == 'parameter':
                    node_data['children'][child_name] = data
                elif data['type'] == 'scale':
                    node_data['children'][child_name] = data
        elif os.path.isdir(child_path):
            child_name = os.path.basename(child_path)
            node_data['children'][child_name] = parse_dir(child_path)
        else:
            raise ValueError('Unexpected item {}'.format(child_path))

    return node_data


def load_legislation(path_list):
    '''load_legislation() : load YAML directories

    If several directories are parsed, newer children with the same name are not merged but overwrite previous ones.
    '''

    assert len(path_list) >= 1, 'Trying to load parameters with no YAML directory given !'

    legislations = []
    for path in path_list:
        legislation = parse_dir(path)
        legislations.append(legislation)

    base_legislation = legislations[0]
    base_children = base_legislation['children']
    for i in range(1, len(legislations)):
        legislation = legislations[i]
        new_children = legislation['children']
        base_children.update(new_children)

    return base_legislation
