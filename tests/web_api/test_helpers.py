import os

from openfisca_core.parameters import load_parameter_file
from openfisca_web_api.loader import parameters

dir_path = os.path.join(os.path.dirname(__file__), "assets")


def test_build_api_values_history() -> None:
    file_path = os.path.join(dir_path, "test_helpers.yaml")
    parameter = load_parameter_file(name="dummy_name", file_path=file_path)

    values = {
        "2017-01-01": 0.02,
        "2015-01-01": 0.04,
        "2013-01-01": 0.03,
    }
    assert parameters.build_api_values_history(parameter) == values


def test_build_api_values_history_with_stop_date() -> None:
    file_path = os.path.join(dir_path, "test_helpers_with_stop_date.yaml")
    parameter = load_parameter_file(name="dummy_name", file_path=file_path)

    values = {
        "2018-01-01": None,
        "2017-01-01": 0.02,
        "2015-01-01": 0.04,
        "2013-01-01": 0.03,
    }

    assert parameters.build_api_values_history(parameter) == values


def test_get_value() -> None:
    values = {"2013-01-01": 0.03, "2017-01-01": 0.02, "2015-01-01": 0.04}

    assert parameters.get_value("2013-01-01", values) == 0.03
    assert parameters.get_value("2014-01-01", values) == 0.03
    assert parameters.get_value("2015-02-01", values) == 0.04
    assert parameters.get_value("2016-12-31", values) == 0.04
    assert parameters.get_value("2017-01-01", values) == 0.02
    assert parameters.get_value("2018-01-01", values) == 0.02


def test_get_value_with_none() -> None:
    values = {"2015-01-01": 0.04, "2017-01-01": None}

    assert parameters.get_value("2016-12-31", values) == 0.04
    assert parameters.get_value("2017-01-01", values) is None
    assert parameters.get_value("2011-01-01", values) is None
