import json
from http import client

import dpath.util
import pytest
from openapi_spec_validator import OpenAPIV30SpecValidator


def assert_items_equal(x, y) -> None:
    assert sorted(x) == sorted(y)


def test_return_code(test_client) -> None:
    openAPI_response = test_client.get("/spec")
    assert openAPI_response.status_code == client.OK


@pytest.fixture(scope="module")
def body(test_client):
    openAPI_response = test_client.get("/spec")
    return json.loads(openAPI_response.data.decode("utf-8"))


def test_paths(body) -> None:
    assert_items_equal(
        body["paths"],
        [
            "/parameter/{parameterID}",
            "/parameters",
            "/variable/{variableID}",
            "/variables",
            "/entities",
            "/trace",
            "/calculate",
            "/spec",
        ],
    )


def test_entity_definition(body) -> None:
    assert "parents" in dpath.util.get(body, "components/schemas/Household/properties")
    assert "children" in dpath.util.get(body, "components/schemas/Household/properties")
    assert "salary" in dpath.util.get(body, "components/schemas/Person/properties")
    assert "rent" in dpath.util.get(body, "components/schemas/Household/properties")
    assert (
        dpath.util.get(
            body,
            "components/schemas/Person/properties/salary/additionalProperties/type",
        )
        == "number"
    )


def test_situation_definition(body) -> None:
    situation_input = body["components"]["schemas"]["SituationInput"]
    situation_output = body["components"]["schemas"]["SituationOutput"]
    for situation in situation_input, situation_output:
        assert "households" in dpath.util.get(situation, "/properties")
        assert "persons" in dpath.util.get(situation, "/properties")
        assert (
            dpath.util.get(
                situation,
                "/properties/households/additionalProperties/$ref",
            )
            == "#/components/schemas/Household"
        )
        assert (
            dpath.util.get(
                situation,
                "/properties/persons/additionalProperties/$ref",
            )
            == "#/components/schemas/Person"
        )


def test_respects_spec(body) -> None:
    assert not list(OpenAPIV30SpecValidator(body).iter_errors())
