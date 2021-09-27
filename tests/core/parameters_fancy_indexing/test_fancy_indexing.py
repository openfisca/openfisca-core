import os
import re

import numpy as np
import pytest


from openfisca_core.tools import assert_near
from openfisca_core.parameters import ParameterNode, Parameter, ParameterNotFound
from openfisca_core.model_api import *  # noqa

LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))

parameters = ParameterNode(directory_path = LOCAL_DIR)

P = parameters.rate('2015-01-01')


def get_message(error):
    return error.args[0]


def test_on_leaf():
    zone = np.asarray(['z1', 'z2', 'z2', 'z1'])
    assert_near(P.single.owner[zone], [100, 200, 200, 100])


def test_on_node():
    housing_occupancy_status = np.asarray(['owner', 'owner', 'tenant', 'tenant'])
    node = P.single[housing_occupancy_status]
    assert_near(node.z1, [100, 100, 300, 300])
    assert_near(node['z1'], [100, 100, 300, 300])


def test_double_fancy_indexing():
    zone = np.asarray(['z1', 'z2', 'z2', 'z1'])
    housing_occupancy_status = np.asarray(['owner', 'owner', 'tenant', 'tenant'])
    assert_near(P.single[housing_occupancy_status][zone], [100, 200, 400, 300])


def test_double_fancy_indexing_on_node():
    family_status = np.asarray(['single', 'couple', 'single', 'couple'])
    housing_occupancy_status = np.asarray(['owner', 'owner', 'tenant', 'tenant'])
    node = P[family_status][housing_occupancy_status]
    assert_near(node.z1, [100, 500, 300, 700])
    assert_near(node['z1'], [100, 500, 300, 700])
    assert_near(node.z2, [200, 600, 400, 800])
    assert_near(node['z2'], [200, 600, 400, 800])


def test_triple_fancy_indexing():
    family_status = np.asarray(['single', 'single', 'single', 'single', 'couple', 'couple', 'couple', 'couple'])
    housing_occupancy_status = np.asarray(['owner', 'owner', 'tenant', 'tenant', 'owner', 'owner', 'tenant', 'tenant'])
    zone = np.asarray(['z1', 'z2', 'z1', 'z2', 'z1', 'z2', 'z1', 'z2'])
    assert_near(P[family_status][housing_occupancy_status][zone], [100, 200, 300, 400, 500, 600, 700, 800])


def test_wrong_key():
    zone = np.asarray(['z1', 'z2', 'z2', 'toto'])
    with pytest.raises(ParameterNotFound) as e:
        P.single.owner[zone]
    assert "'rate.single.owner.toto' was not found" in get_message(e.value)


def test_inhomogenous():
    parameters = ParameterNode(directory_path = LOCAL_DIR)
    parameters.rate.couple.owner.add_child('toto', Parameter('toto', {
        "values": {
            "2015-01-01": {
                "value": 1000
                },
            }
        }))

    P = parameters.rate('2015-01-01')
    housing_occupancy_status = np.asarray(['owner', 'owner', 'tenant', 'tenant'])
    with pytest.raises(ValueError) as error:
        P.couple[housing_occupancy_status]
    assert "'rate.couple.owner.toto' exists" in get_message(error.value)
    assert "'rate.couple.tenant.toto' doesn't" in get_message(error.value)


def test_inhomogenous_2():
    parameters = ParameterNode(directory_path = LOCAL_DIR)
    parameters.rate.couple.tenant.add_child('toto', Parameter('toto', {
        "values": {
            "2015-01-01": {
                "value": 1000
                },
            }
        }))

    P = parameters.rate('2015-01-01')
    housing_occupancy_status = np.asarray(['owner', 'owner', 'tenant', 'tenant'])
    with pytest.raises(ValueError) as e:
        P.couple[housing_occupancy_status]
    assert "'rate.couple.tenant.toto' exists" in get_message(e.value)
    assert "'rate.couple.owner.toto' doesn't" in get_message(e.value)


def test_inhomogenous_3():
    parameters = ParameterNode(directory_path = LOCAL_DIR)
    parameters.rate.couple.tenant.add_child('z4', ParameterNode('toto', data = {
        'amount': {
            'values': {
                "2015-01-01": {'value': 550},
                "2016-01-01": {'value': 600}
                }
            }
        }))

    P = parameters.rate('2015-01-01')
    zone = np.asarray(['z1', 'z2', 'z2', 'z1'])
    with pytest.raises(ValueError) as e:
        P.couple.tenant[zone]
    assert "'rate.couple.tenant.z4' is a node" in get_message(e.value)
    assert re.findall(r"'rate.couple.tenant.z(1|2|3)' is not", get_message(e.value))


P_2 = parameters.local_tax('2015-01-01')


def test_with_properties_starting_by_number():
    city_code = np.asarray(['75012', '75007', '75015'])
    assert_near(P_2[city_code], [100, 300, 200])


P_3 = parameters.bareme('2015-01-01')


def test_with_bareme():
    city_code = np.asarray(['75012', '75007', '75015'])
    with pytest.raises(NotImplementedError) as e:
        P_3[city_code]
    assert re.findall(r"'bareme.7501\d' is a 'MarginalRateTaxScale'", get_message(e.value))
    assert "has not been implemented" in get_message(e.value)


def test_with_enum():

    class TypesZone(Enum):
        z1 = "Zone 1"
        z2 = "Zone 2"

    zone = np.asarray([TypesZone.z1, TypesZone.z2, TypesZone.z2, TypesZone.z1])
    assert_near(P.single.owner[zone], [100, 200, 200, 100])
