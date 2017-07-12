# -*- coding: utf-8 -*-

import os
import time
import json
import logging

from . import subject


log = logging.getLogger(__name__)


def time_requests(nb_requests, request):
    start_time = time.time()

    for i in range(nb_requests):
        yield request

    exec_time = time.time() - start_time
    log.info('{:2.6f} s'.format(exec_time))


def test_multiple_requests__variables():
    time_requests(100, subject.get('/variables'))


def post_json(data = None, file = None):
    if file:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', file)
        with open(file_path, 'r') as file:
            data = file.read()
    return subject.post('/calculate', data = data, content_type = 'application/json')


def test_multiple_requests__calculate():
    simulation_json = json.dumps({
        "persons": {
            "bill": {
                "birth": {
                    "2017-12": "1980-01-01"
                    },
                "age": {
                    "2017-12": None
                    },
                "salary": {
                    "2017-12": 2000
                    },
                "basic_income": {
                    "2017-12": None
                    },
                "income_tax": {
                    "2017-12": None
                    }
                },
            "bob": {
                "salary": {
                    "2017-12": 15000
                    },
                "basic_income": {
                    "2017-12": None
                    },
                "social_security_contribution": {
                    "2017-12": None
                    }
                },
            },
        "households": {
            "first_household": {
                "parents": ['bill', 'bob'],
                "housing_tax": {
                    "2017": None
                    },
                "accomodation_size": {
                    "2017-01": 300
                    }
                },
            }
        })

    time_requests(100, post_json(simulation_json))
