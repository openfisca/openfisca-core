# -*- coding: utf-8 -*-

import pytest

from openfisca_core.parameters import ParameterNode, Scale

from openfisca_web_api.loader.parameters import build_api_scale, walk_node


def test_build_rate_scale():
    '''Extracts a 'rate' children from a bracket collection'''
    data = {'brackets': [{'rate': {'2014-01-01': {'value': 0.5}}, 'threshold': {'2014-01-01': {'value': 1}}}]}
    rate = Scale('this rate', data, None)
    assert build_api_scale(rate, 'rate') == {'2014-01-01': {1: 0.5}}


def test_build_amount_scale():
    '''Extracts an 'amount' children from a bracket collection'''
    data = {'brackets': [{'amount': {'2014-01-01': {'value': 0}}, 'threshold': {'2014-01-01': {'value': 1}}}]}
    rate = Scale('that amount', data, None)
    assert build_api_scale(rate, 'amount') == {'2014-01-01': {1: 0}}


@pytest.fixture
def walk_node_args():
    parameters = []
    path_fragments = []
    country_package_metadata = {'location': 'foo', 'version': '1', 'repository_url': 'foo'}

    return parameters, path_fragments, country_package_metadata


def test_walk_node_rate_scale(walk_node_args):
    '''Serializes a 'rate' parameter node'''
    root_node = ParameterNode(data = {})
    data = {'brackets': [{'rate': {'2014-01-01': {'value': 0.5}}, 'threshold': {'2014-01-01': {'value': 1}}}]}
    scale = Scale('this rate', data, None)
    root_node.children['rate'] = scale
    parameters = walk_node(root_node, *walk_node_args)
    assert parameters == [{'description': None, 'id': 'rate', 'metadata': {}, 'brackets': {'2014-01-01': {1: 0.5}}}]


def test_walk_node_amount_scale(walk_node_args):
    '''Serializes an 'amount' parameter node'''
    root_node = ParameterNode(data = {})
    data = {'brackets': [{'amount': {'2014-01-01': {'value': 0}}, 'threshold': {'2014-01-01': {'value': 1}}}]}
    scale = Scale('that amount', data, None)
    root_node.children['amount'] = scale
    parameters = walk_node(root_node, *walk_node_args)
    assert parameters == [{'description': None, 'id': 'amount', 'metadata': {}, 'brackets': {'2014-01-01': {1: 0}}}]
