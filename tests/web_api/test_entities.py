import json
from http import client

from openfisca_country_template import entities

# /entities


def test_return_code(test_client) -> None:
    entities_response = test_client.get("/entities")
    assert entities_response.status_code == client.OK


def test_response_data(test_client) -> None:
    entities_response = test_client.get("/entities")
    entities_dict = json.loads(entities_response.data.decode("utf-8"))
    test_documentation = entities.Household.doc.strip()

    assert entities_dict["household"] == {
        "description": "All the people in a family or group who live together in the same place.",
        "documentation": test_documentation,
        "plural": "households",
        "roles": {
            "child": {
                "description": "The non-adults of the household.",
                "plural": "children",
            },
            "adult": {
                "description": "The adults of the household.",
                "plural": "adults",
            },
        },
    }
