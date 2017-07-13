# -*- coding: utf-8 -*-

import time
import json

from openfisca_web_api_preview.app import create_app


TEST_COUNTRY_PACKAGE_NAME = 'openfisca_country_template'
TRACKER_URL = 'https://openfisca.innocraft.cloud/piwik.php'
TRACKER_IDSITE = 1

api_with_tracking = create_app(TEST_COUNTRY_PACKAGE_NAME, TRACKER_URL, TRACKER_IDSITE).test_client()

api_without_tracking = create_app(TEST_COUNTRY_PACKAGE_NAME).test_client()


def time_requests(nb_requests, request_call, tracking):
    start_time = time.time()

    for i in range(nb_requests):
        if tracking:
            request_call(api_with_tracking)
        else:
            request_call(api_without_tracking)

    exec_time = time.time() - start_time
    return exec_time


def request_variables(api):
    api.get('/variables')


def request_calculate(api):
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
    return api.post('/calculate', data = simulation_json, content_type = 'application/json')


def test_multiple_requests__variables():
    time_requests(100, request_variables)


def test_multiple_requests__calculate():
    time_requests(100, request_calculate)


print("/variables route without tracking")
variables_without_tracking_time = time_requests(100, request_variables, tracking = False)
print('100 calls take {:2.6f} s'.format(variables_without_tracking_time))

print("/calculate route without tracking")
variables_without_tracking_time = time_requests(100, request_variables, tracking = False)
print('100 calls take {:2.6f} s'.format(variables_without_tracking_time))

print("/variables route with tracking")
variables_without_tracking_time = time_requests(100, request_variables, tracking = True)
print('100 calls take {:2.6f} s'.format(variables_without_tracking_time))

print("/calculate route with tracking")
variables_without_tracking_time = time_requests(100, request_variables, tracking = True)
print('100 calls take {:2.6f} s'.format(variables_without_tracking_time))
