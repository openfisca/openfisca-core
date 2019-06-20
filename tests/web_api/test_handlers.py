# -*- coding: utf-8 -*-

from openfisca_web_api.handlers import get_flat_trace

def test_flat_trace():
    tree = {
        'name': 'a',
        'period': 2018,
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
    assert trace['a<2018>']['dependencies'] == ['b<2019>']
    assert trace['b<2019>']['dependencies'] == []
