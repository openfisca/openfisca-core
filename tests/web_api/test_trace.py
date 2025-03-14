import copy
import json
from http import client

import dpath

from openfisca_country_template.situation_examples import couple, single


def assert_items_equal(x, y) -> None:
    assert set(x) == set(y)


def test_trace_basic(test_client) -> None:
    simulation_json = json.dumps(single)
    response = test_client.post(
        "/trace",
        data=simulation_json,
        content_type="application/json",
    )
    assert response.status_code == client.OK
    response_json = json.loads(response.data.decode("utf-8"))
    disposable_income_value = dpath.get(
        response_json,
        "trace/disposable_income<2017-01>/value",
    )
    assert isinstance(disposable_income_value, list)
    assert isinstance(disposable_income_value[0], float)
    disposable_income_dep = dpath.get(
        response_json,
        "trace/disposable_income<2017-01>/dependencies",
    )
    assert_items_equal(
        disposable_income_dep,
        [
            "basic_income<2017-01>",
            "capital_returns<2017-01>",
            "housing_allowance<2017-01>",
            "housing_tax<2017>",
            "income_tax<2017-01>",
            "parenting_allowance<2017-01>",
            "pension<2017-01>",
            "salary<2017-01>",
            "social_security_contribution<2017-01>",
        ],
    )
    basic_income_dep = dpath.get(
        response_json,
        "trace/basic_income<2017-01>/dependencies",
    )
    assert_items_equal(basic_income_dep, ["age<2017-01>"])


def test_trace_enums(test_client) -> None:
    new_single = copy.deepcopy(single)
    new_single["households"]["_"]["housing_occupancy_status"] = {"2017-01": None}
    simulation_json = json.dumps(new_single)
    response = test_client.post(
        "/trace",
        data=simulation_json,
        content_type="application/json",
    )
    response_json = json.loads(response.data)
    housing_status = dpath.get(
        response_json,
        "trace/housing_occupancy_status<2017-01>/value",
    )
    assert housing_status[0] == "tenant"  # The default value


def test_entities_description(test_client) -> None:
    simulation_json = json.dumps(couple)
    response = test_client.post(
        "/trace",
        data=simulation_json,
        content_type="application/json",
    )
    response_json = json.loads(response.data.decode("utf-8"))
    assert_items_equal(
        dpath.get(response_json, "entitiesDescription/persons"),
        ["Javier", "Alicia"],
    )


def test_root_nodes(test_client) -> None:
    simulation_json = json.dumps(couple)
    response = test_client.post(
        "/trace",
        data=simulation_json,
        content_type="application/json",
    )
    response_json = json.loads(response.data.decode("utf-8"))
    assert_items_equal(
        dpath.get(response_json, "requestedCalculations"),
        [
            "disposable_income<2017-01>",
            "total_benefits<2017-01>",
            "total_taxes<2017-01>",
        ],
    )


def test_str_variable(test_client) -> None:
    new_couple = copy.deepcopy(couple)
    new_couple["households"]["_"]["postal_code"] = {"2017-01": None}
    simulation_json = json.dumps(new_couple)

    response = test_client.post(
        "/trace",
        data=simulation_json,
        content_type="application/json",
    )

    assert response.status_code == client.OK


def test_trace_parameters(test_client) -> None:
    new_couple = copy.deepcopy(couple)
    new_couple["households"]["_"]["housing_tax"] = {"2017": None}
    simulation_json = json.dumps(new_couple)

    response = test_client.post(
        "/trace",
        data=simulation_json,
        content_type="application/json",
    )
    response_json = json.loads(response.data.decode("utf-8"))

    assert len(dpath.get(response_json, "trace/housing_tax<2017>/parameters")) > 0
    taxes__housing_tax__minimal_amount = dpath.get(
        response_json,
        "trace/housing_tax<2017>/parameters/taxes.housing_tax.minimal_amount<2017-01-01>",
    )
    assert taxes__housing_tax__minimal_amount == 200
