# -*- coding: utf-8 -*-

from http import client
import json

from openfisca_country_template import entities


# /entities


def test_return_code(test_client):
    entities_response = test_client.get("/entities")
    assert entities_response.status_code == client.OK


def test_response_data(test_client):
    entities_response = test_client.get("/entities")
    entities_dict = json.loads(entities_response.data.decode("utf-8"))
    test_documentation = entities.Household.doc.strip()

    assert entities_dict["household"] == {
        "description": "All the people in a family or group who live together in the same place.",
        "documentation": test_documentation,
        "plural": "households",
        "roles": {
            "child": {
                "description": "Other individuals living in the household.",
                "plural": "children",
            },
            "parent": {
                "description": "The one or two adults in charge of the household.",
                "plural": "parents",
                "max": 2,
            },
        },
    }
