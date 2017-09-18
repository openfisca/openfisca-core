# -*- coding: utf-8 -*-

import numpy as np
from nose.tools import raises

from openfisca_core.tools import assert_near
from openfisca_core.parameters import ParameterNode, ParameterNodeAtInstant

node = ParameterNode('taux', data = {
    'z1': {
      'values': {
        "2015-01-01": {'value': 600},
        }
      },
    'z2': {
      'values': {
        "2015-01-01": {'value': 400},
        }
      },
    })

parameters = node._get_at_instant('2015-01-01')

def test_on_leaf():
    vector = np.asarray(['z1', 'z2', 'z2', 'z1'])
    assert_near(parameters[vector], [600, 400, 400, 600])



# def test_inhomogenous():
#     # Last field is a subnode, but doesn't have the same structure
#     # vector = np.asarray(['zone1', 'zone2', 'colocation'])
#     vector_2 = np.asarray(['toto', 'zone2', 'zone1'])
#     import nose.tools; nose.tools.set_trace(); import ipdb; ipdb.set_trace()
#     loyers_plafond[vector_2].personnes_seules:
