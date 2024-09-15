import os

import numpy

from openfisca_core.parameters import ParameterNode
from openfisca_core.tools import assert_near

from openfisca_core.model_api import *  # noqa

LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))

parameters = ParameterNode(directory_path=LOCAL_DIR)


def get_message(error):
    return error.args[0]


def test_on_leaf():
    parameter_at_instant = parameters.full_rate_required_duration("1995-01-01")
    birthdate = numpy.array(
        ["1930-01-01", "1935-01-01", "1940-01-01", "1945-01-01"], dtype="datetime64[D]"
    )
    assert_near(
        parameter_at_instant.contribution_quarters_required_by_birthdate[birthdate],
        [150, 152, 157, 160],
    )


def test_on_node():
    birthdate = numpy.array(
        ["1950-01-01", "1953-01-01", "1956-01-01", "1959-01-01"], dtype="datetime64[D]"
    )
    parameter_at_instant = parameters.full_rate_age("2012-03-01")
    node = parameter_at_instant.full_rate_age_by_birthdate[birthdate]
    assert_near(node.year, [65, 66, 67, 67])
    assert_near(node.month, [0, 2, 0, 0])


# def test_inhomogenous():
#     birthdate = numpy.array(['1930-01-01', '1935-01-01', '1940-01-01', '1945-01-01'], dtype = 'datetime64[D]')
#     parameter_at_instant = parameters..full_rate_age('2011-01-01')
#     parameter_at_instant.full_rate_age_by_birthdate[birthdate]
#     with pytest.raises(ValueError) as error:
#         parameter_at_instant.full_rate_age_by_birthdate[birthdate]
#     assert "Cannot use fancy indexing on parameter node '.full_rate_age.full_rate_age_by_birthdate'" in get_message(error.value)
