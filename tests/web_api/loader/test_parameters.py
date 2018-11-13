# -*- coding: utf-8 -*-

from openfisca_web_api.loader.parameters import walk_node

from openfisca_core.parameters import (
    ParameterNode,
    Scale,
    )


def test_rate_tax_scale_serialization():
    parameters = []
    metadata = {'location': 'foo', 'version': '1', 'repository_url': 'foo'}
    root_node = ParameterNode(data = {})
    amount_rate_data = {'brackets': [{'rate': {'2014-01-01': {'value': 0.5}}, 'threshold': {'2014-01-01': {'value': 1}}}]}
    rate = Scale('scale', amount_rate_data, 'foo')
    root_node.children['rate'] = rate
    walk_node(root_node, parameters, [], metadata)
    assert parameters == [{'description': None, 'id': 'rate', 'metadata': {}, 'source': 'foo/blob/1', 'brackets': {'2014-01-01': {1: 0.5}}}]


def test_amount_tax_scale_serialization():
    parameters = []
    metadata = {'location': 'foo', 'version': '1', 'repository_url': 'foo'}
    root_node = ParameterNode(data = {})
    amount_scale_data = {'brackets': [{'amount': {'2014-01-01': {'value': 0}}, 'threshold': {'2014-01-01': {'value': 1}}}]}
    amount = Scale('scale', amount_scale_data, 'foo')
    root_node.children['amount'] = amount
    walk_node(root_node, parameters, [], metadata)
    assert parameters == [{'description': None, 'id': 'amount', 'metadata': {}, 'source': 'foo/blob/1', 'brackets': {'2014-01-01': {1: 0}}}]
