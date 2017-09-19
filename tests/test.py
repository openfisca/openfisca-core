# -*- coding: utf-8 -*-

import numpy as np
from nose.tools import raises

from openfisca_core.tools import assert_near
from openfisca_core.parameters import ParameterNode, ParameterNodeAtInstant

node = ParameterNode('rate', data = {
  "single": {
    "owner": {
      "z1": {
        "values": {
          "2015-01-01": {
            "value": 100
          },
        }
      },
      "z2": {
        "values": {
          "2015-01-01": {
            "value": 200
          },
        }
      },
    },
    "tenant": {
      "z1": {
        "values": {
          "2015-01-01": {
            "value": 300
          },
        }
      },
      "z2": {
        "values": {
          "2015-01-01": {
            "value": 400
          },
        }
      },
    }
  },
  "couple": {
    "owner": {
      "z1": {
        "values": {
          "2015-01-01": {
            "value": 500
          },
        }
      },
      "z2": {
        "values": {
          "2015-01-01": {
            "value": 600
          },
        }
      },
    },
    "tenant": {
      "z1": {
        "values": {
          "2015-01-01": {
            "value": 700
          },
        }
      },
      "z2": {
        "values": {
          "2015-01-01": {
            "value": 800
          },
        }
      },
    }
  }
})

P = node._get_at_instant('2015-01-01')


def test_on_leaf():
    zone = np.asarray(['z1', 'z2', 'z2', 'z1'])
    assert_near(P.single.owner[zone], [100, 200, 200, 100])


def test_on_node():
    housing_occupancy_status = np.asarray(['owner', 'owner', 'tenant', 'tenant'])
    assert_near(P.single[housing_occupancy_status].z1, [100,  100, 300, 300])
    assert_near(P.single[housing_occupancy_status]['z1'], [100,  100, 300, 300])

# @raises(KeyError)
# def test_wrong_key():
#     vector = np.asarray(['personnes_seules', 'couples', 'toto'])
#     loyers_plafond.zone1[vector]


# def test_inhomogenous():
#     # Last field is a subnode, but doesn't have the same structure
#     # vector = np.asarray(['zone1', 'zone2', 'colocation'])
#     vector_2 = np.asarray(['toto', 'zone2', 'zone1'])
#     import nose.tools; nose.tools.set_trace(); import ipdb; ipdb.set_trace()
#     loyers_plafond[vector_2].personnes_seules:
