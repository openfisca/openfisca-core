import numpy

from openfisca_core.tools import assert_near


def test_date():
    assert_near(numpy.array("2012-03-24", dtype = "datetime64[D]"), "2012-03-24")


def test_enum(tax_benefit_system):
    possible_values = tax_benefit_system.variables["housing_occupancy_status"].possible_values
    value = possible_values.encode(numpy.array(["tenant"]))
    expected_value = "tenant"
    assert_near(value, expected_value)


def test_enum_2(tax_benefit_system):
    possible_values = tax_benefit_system.variables["housing_occupancy_status"].possible_values
    value = possible_values.encode(numpy.array(["tenant", "owner"]))
    expected_value = ["tenant", "owner"]
    assert_near(value, expected_value)
