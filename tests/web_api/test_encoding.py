# -*- coding: utf-8 -*-

from httplib import BAD_REQUEST, OK, NOT_FOUND
import json
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
            "bob": {}
        },
        "households": {
            "_": {
                "housing_occupancy_status": {
                    "2017-07": "Locataire ou sous-locataire d‘un logement loué vide non-HLM"
    
                },
                "parent": [
                    "bob"
                ],
                "children": [ ]
            }
        }
    })

    response = post_json(simulation_json)
    log.info(response.data)
    # json_response = json.loads(response.data, encoding='utf-8')
    assert_equal(response.status_code, OK, response.data)
