# -*- coding: utf-8 -*-

from openfisca_web_api.handlers import get_flat_trace


def test_flat_trace():
    tree = {
        'name': 'a',
        'period': 2019,
        'children': [
            {
                'name': 'b',
                'period': 2019,
                'children': [],
                'parameters': [],
                'value': None
                }
            ],
        'parameters': [],
        'value': None
        }

    trace = get_flat_trace(tree)

    assert len(trace) == 2
    assert trace['a<2019>']['dependencies'] == ['b<2019>']
    assert trace['b<2019>']['dependencies'] == []


def test_flat_trace_with_cache():
    tree = {
    'children': [
        {
            'children': [{
                'children': [],
                'name': 'c',
                'parameters': [],
                'period': 2019,
                'value': None
                }
            ],
            'name': 'b',
            'parameters': [],
            'period': 2019,
            'value': None
        },
        {
            'children': [],
            'name': 'b',
            'parameters': [],
            'period': 2019,
            'value': None
        }
    ],
    'name': 'a',
    'parameters': [],
    'period': 2019,
    'value': None
    }

    trace = get_flat_trace(tree)

    assert trace['b<2019>']['dependencies'] == ['c<2019>']
