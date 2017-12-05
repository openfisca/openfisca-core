# -*- coding: utf-8 -*-

from httplib import BAD_REQUEST, OK
import json
import os
from nose.tools import assert_equal
from . import subject
import logging


log = logging.getLogger(__name__)


def post_json(data = None, file = None):
    if file:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', file)
        with open(file_path, 'r') as file:
            data = file.read()
    return subject.post('/calculate', data = data, content_type = 'application/json')


def test_encoding():
    simulation_json = json.dumps({
        "persons": {
            "O‘Ryan": {},
            "Renée": {}
        },
        "households": {
            "_": {
                "housing_occupancy_status": {
                    "2017-07": "Locataire ou sous-locataire d‘un logement loué vide non-HLM"
    
                },
                "parent": [
                    "O‘Ryan",
                    "Renée"
                ],
                "children": [ ]
            }
        }
    })

    # No UnicodeDecodeError
    expected_response = "'Locataire ou sous-locataire d‘un logement loué vide non-HLM' is not a valid value for 'housing_occupancy_status'. Possible values are ['Tenant', 'Owner', 'Free logder', 'Homeless']."
    response = post_json(simulation_json)
    assert expected_response in response.data, expected_response + os.linesep + " NOT FOUND IN: " + os.linesep + response.data
    assert_equal(response.status_code, BAD_REQUEST, response.data)
