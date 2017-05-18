# -*- coding: utf-8 -*-


import collections
import copy
from xml.etree import ElementTree

from . import conv, decompositionsxml, legislations


def calculate(simulations, decomposition_json):

    def new_test_case_array(holder, array):
        entity_step_size = holder.entity.step_size
        return array.reshape([holder.simulation.steps_count, entity_step_size]).sum(1)

    response_json = copy.deepcopy(decomposition_json)  # Use decomposition as a skeleton for response.
    for node in iter_decomposition_nodes(response_json, children_first = True):
        children = node.get('children')
        if children:
            node['values'] = map(lambda *l: sum(l), *(
                child['values']
                for child in children
                ))
        else:
            node['values'] = values = []
            for simulation_index, simulation in enumerate(simulations):
                try:
                    array = simulation.calculate_output(node['code'], simulation.period)
                except legislations.ParameterNotFound as exc:
                    exc.simulation_index = simulation_index
                    raise
                holder = simulation.get_holder(node['code'])
                column = holder.column
                values.extend(
                    column.transform_value_to_json(value)
                    for value in new_test_case_array(holder, array).tolist()
                    )
    return response_json


def get_decomposition_json(tax_benefit_system, xml_file_path = None):
    if xml_file_path is None:
        xml_file_path = tax_benefit_system.decomposition_file_path
    decomposition_tree = ElementTree.parse(xml_file_path)
    decomposition_xml_json = conv.check(decompositionsxml.xml_decomposition_to_json)(decomposition_tree.getroot(),
        state = conv.State)
    decomposition_xml_json = conv.check(decompositionsxml.make_validate_node_xml_json(tax_benefit_system))(
        decomposition_xml_json, state = conv.State)
    decomposition_json = decompositionsxml.transform_node_xml_json_to_json(decomposition_xml_json)
    return decomposition_json


def iter_decomposition_nodes(node_or_nodes, children_first = False):
    if isinstance(node_or_nodes, list):
        for node in node_or_nodes:
            for sub_node in iter_decomposition_nodes(node, children_first = children_first):
                yield sub_node
    else:
        if not children_first:
            yield node_or_nodes
        children = node_or_nodes.get('children')
        if children:
            for child_node in children:
                for sub_node in iter_decomposition_nodes(child_node, children_first = children_first):
                    yield sub_node
        if children_first:
            yield node_or_nodes


def make_validate_node_json(tax_benefit_system):
    def validate_node_json(node, state = None):
        if node is None:
            return None, None
        if state is None:
            state = conv.default_state
        validated_node, errors = conv.pipe(
            conv.condition(
                conv.test_isinstance(list),
                conv.uniform_sequence(
                    validate_node_json,
                    drop_none_items = True,
                    ),
                conv.pipe(
                    conv.condition(
                        conv.test_isinstance(basestring),
                        conv.function(lambda code: dict(code = code)),
                        conv.test_isinstance(dict),
                        ),
                    conv.struct(
                        dict(
                            children = conv.pipe(
                                conv.test_isinstance(list),
                                conv.uniform_sequence(
                                    validate_node_json,
                                    drop_none_items = True,
                                    ),
                                conv.empty_to_none,
                                ),
                            code = conv.pipe(
                                conv.test_isinstance(basestring),
                                conv.cleanup_line,
                                ),
                            ),
                        constructor = collections.OrderedDict,
                        default = conv.noop,
                        drop_none_values = 'missing',
                        keep_value_order = True,
                        ),
                    ),
                ),
            conv.empty_to_none,
            )(node, state = state)
        if validated_node is None or errors is not None:
            return validated_node, errors

        if isinstance(validated_node, dict) and not validated_node.get('children'):
            validated_node, errors = conv.struct(
                dict(
                    code = conv.pipe(
                        conv.test_in(tax_benefit_system.column_by_name),
                        conv.not_none,
                        ),
                    ),
                default = conv.noop,
                )(validated_node, state = state)
        return validated_node, errors

    return validate_node_json
