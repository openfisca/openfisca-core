from __future__ import unicode_literals, print_function, division, absolute_import

import numpy as np

from openfisca_core.tools import assert_near

from ..test_countries import tax_benefit_system


def test_enum():
    possible_values = tax_benefit_system.variables['housing_occupancy_status'].possible_values
    value = possible_values.encode(np.array(['tenant']))
    expected_value = 'tenant'
    assert_near(value, expected_value)


def test_enum_2():
    possible_values = tax_benefit_system.variables['housing_occupancy_status'].possible_values
    value = possible_values.encode(np.array(['tenant', 'owner']))
    expected_value = ['tenant', 'owner']
    assert_near(value, expected_value)
