# -*- coding: utf-8 -*-

from openfisca_web_api.loader.parameters import walk_node
from openfisca_core.parameters import ParameterNode, Scale

def test_amount_scale():
    parameters = []
    metadata = {'location':'foo', 'version':'1', 'repository_url':'foo'}
    root_node = ParameterNode(data = {})
    amount_scale_data = {'brackets':[{'amount':{'2014-01-01':{'value':0}},'threshold':{'2014-01-01':{'value':1}}}]}
    scale = Scale('scale', amount_scale_data, 'foo')
    root_node.children['scale'] = scale
    walk_node(root_node, parameters, [], metadata)
    assert parameters == [{'description': None, 'id': 'scale', 'metadata': {}, 'source': 'foo/blob/1', 'brackets': {'2014-01-01': {1: 0}}}]
