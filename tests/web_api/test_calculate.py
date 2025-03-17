import copy
import json
import os
from http import client

import dpath
import pytest

from openfisca_country_template.situation_examples import couple


def post_json(client, data=None, file=None):
    if file:
        file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "assets",
            file,
        )
        with open(file_path) as file:
            data = file.read()
    return client.post("/calculate", data=data, content_type="application/json")


def check_response(
    client, data, expected_error_code, path_to_check, content_to_check
) -> None:
    response = post_json(client, data)
    assert response.status_code == expected_error_code
    json_response = json.loads(response.data.decode("utf-8"))
    if path_to_check:
        content = dpath.get(json_response, path_to_check)
        assert content_to_check in content


@pytest.mark.parametrize(
    "test",
    [
        ('{"a" : "x", "b"}', client.BAD_REQUEST, "error", "Invalid JSON"),
        ('["An", "array"]', client.BAD_REQUEST, "error", "Invalid type"),
        ('{"persons": {}}', client.BAD_REQUEST, "persons", "At least one person"),
        (
            '{"persons": {"bob": {}}, "unknown_entity": {}}',
            client.BAD_REQUEST,
            "unknown_entity",
            "entities are not found",
        ),
        (
            '{"persons": {"bob": {}}, "households": {"dupont": {"adults": {}}}}',
            client.BAD_REQUEST,
            "households/dupont/adults",
            "type",
        ),
        (
            '{"persons": {"bob": {"unknown_variable": {}}}}',
            client.NOT_FOUND,
            "persons/bob/unknown_variable",
            "You tried to calculate or to set",
        ),
        (
            '{"persons": {"bob": {"housing_allowance": {}}}}',
            client.BAD_REQUEST,
            "persons/bob/housing_allowance",
            "You tried to compute the variable 'housing_allowance' for the entity 'persons'",
        ),
        (
            '{"persons": {"bob": {"salary": 4000 }}}',
            client.BAD_REQUEST,
            "persons/bob/salary",
            "period",
        ),
        (
            '{"persons": {"bob": {"salary": {"2017-01": "toto"} }}}',
            client.BAD_REQUEST,
            "persons/bob/salary/2017-01",
            "expected type number",
        ),
        (
            '{"persons": {"bob": {"salary": {"2017-01": {}} }}}',
            client.BAD_REQUEST,
            "persons/bob/salary/2017-01",
            "expected type number",
        ),
        (
            '{"persons": {"bob": {"age": {"2017-01": "toto"} }}}',
            client.BAD_REQUEST,
            "persons/bob/age/2017-01",
            "expected type integer",
        ),
        (
            '{"persons": {"bob": {"birth": {"2017-01": "toto"} }}}',
            client.BAD_REQUEST,
            "persons/bob/birth/2017-01",
            "Can't deal with date",
        ),
        (
            '{"persons": {"bob": {}}, "households": {"household": {"adults": ["unexpected_person_id"]}}}',
            client.BAD_REQUEST,
            "households/household/adults",
            "has not been declared in persons",
        ),
        (
            '{"persons": {"bob": {}}, "households": {"household": {"adults": ["bob", "bob"]}}}',
            client.BAD_REQUEST,
            "households/household/adults",
            "has been declared more than once",
        ),
        (
            '{"persons": {"bob": {}}, "households": {"household": {"adults": ["bob", {}]}}}',
            client.BAD_REQUEST,
            "households/household/adults/1",
            "Invalid type",
        ),
        (
            '{"persons": {"bob": {"salary": {"invalid period": 2000 }}}}',
            client.BAD_REQUEST,
            "persons/bob/salary",
            "Expected a period",
        ),
        (
            '{"persons": {"bob": {"salary": {"invalid period": null }}}}',
            client.BAD_REQUEST,
            "persons/bob/salary",
            "Expected a period",
        ),
        (
            '{"persons": {"bob": {"basic_income": {"2017": 2000 }}}, "households": {"household": {"adults": ["bob"]}}}',
            client.BAD_REQUEST,
            "persons/bob/basic_income/2017",
            '"basic_income" can only be set for one month',
        ),
        (
            '{"persons": {"bob": {"salary": {"ETERNITY": 2000 }}}, "households": {"household": {"adults": ["bob"]}}}',
            client.BAD_REQUEST,
            "persons/bob/salary/ETERNITY",
            "salary is only defined for months",
        ),
    ],
)
def test_responses(test_client, test) -> None:
    check_response(test_client, *test)


def test_basic_individual_calculation(test_client) -> None:
    # Arrange
    simulation_json = json.dumps(
        {
            "persons": {
                "bill": {
                    "birth": {"2017-12": "1980-01-01"},
                    "age": {"2017-12": None},
                    "salary": {"2017-12": 2000},
                    "basic_income": {"2017-12": None},
                    "income_tax": {"2017-12": None},
                }
            }
        },
    )

    # Act
    response = post_json(test_client, simulation_json)
    response_json = json.loads(response.data.decode("utf-8"))
    basic_income = dpath.get(response_json, "persons/bill/basic_income/2017-12")
    income_tax = dpath.get(response_json, "persons/bill/income_tax/2017-12")
    age = dpath.get(response_json, "persons/bill/age/2017-12")

    # Assert
    assert response.status_code == client.OK
    assert basic_income == 600  # Universal basic income
    assert income_tax == 300  # 15% of the salary
    assert age == 37
    with pytest.raises(KeyError):
        dpath.get(response_json, "persons/bill0")
    with pytest.raises(KeyError):
        dpath.get(response_json, "households")


def test_basic_group_calculation(test_client) -> None:
    # Arrange
    simulation_json = json.dumps(
        {
            "persons": {
                "bill": {
                    "birth": {"2017-12": "1980-01-01"},
                    "age": {"2017-12": None},
                    "salary": {"2017-12": 2000},
                    "basic_income": {"2017-12": None},
                    "income_tax": {"2017-12": None},
                },
                "bob": {
                    "salary": {"2017-12": 15000},
                    "basic_income": {"2017-12": None},
                    "social_security_contribution": {"2017-12": None},
                },
            },
            "households": {
                "bill&bob": {
                    "adults": ["bill", "bob"],
                    "housing_tax": {"2017": None},
                    "accommodation_size": {"2017-01": 300},
                },
            },
        },
    )

    # Act
    response = post_json(test_client, simulation_json)
    response_json = json.loads(response.data.decode("utf-8"))
    bill_basic_income = dpath.get(response_json, "persons/bill/basic_income/2017-12")
    bill_income_tax = dpath.get(response_json, "persons/bill/income_tax/2017-12")
    bill_age = dpath.get(response_json, "persons/bill/age/2017-12")
    bob_basic_income = dpath.get(response_json, "persons/bob/basic_income/2017-12")
    bob_social_security_contribution = dpath.get(
        response_json,
        "persons/bob/social_security_contribution/2017-12",
    )
    housing_tax = dpath.get(response_json, "households/bill&bob/housing_tax/2017")

    # Assert
    assert response.status_code == client.OK
    assert bill_basic_income == 600  # Universal basic income
    assert bill_income_tax == 300  # 15% of the salary
    assert bill_age == 37
    assert bob_basic_income == 600
    assert bob_social_security_contribution == 816
    assert housing_tax == 3000
    with pytest.raises(KeyError):
        dpath.get(response_json, "persons/bill0")
    with pytest.raises(KeyError):
        dpath.get(response_json, "households/bill&bob0")


def test_axes_individual(test_client) -> None:
    # Arrange
    simulation_json = json.dumps(
        {
            "persons": {
                "bill": {
                    "income_tax": {"2025-03": None},
                    "salary": {"2025-03": None},
                }
            },
            "households": {
                "_": {
                    "adults": ["bill"],
                }
            },
            "axes": [
                [
                    {
                        "count": 3,
                        "name": "capital_returns",
                        "min": 0,
                        "max": 1500,
                        "period": "2025-03",
                    },
                    {
                        "count": 3,
                        "name": "salary",
                        "min": 0,
                        "max": 8500,
                        "period": "2025-03",
                    },
                ]
            ],
        },
    )

    # Act
    response = post_json(test_client, simulation_json)
    response_json = json.loads(response.data.decode("utf-8"))
    income_tax_1 = dpath.get(response_json, "persons/bill0/income_tax/2025-03")
    income_tax_2 = dpath.get(response_json, "persons/bill1/income_tax/2025-03")
    income_tax_3 = dpath.get(response_json, "persons/bill2/income_tax/2025-03")
    salary_1 = dpath.get(response_json, "persons/bill0/salary/2025-03")
    salary_2 = dpath.get(response_json, "persons/bill1/salary/2025-03")
    salary_3 = dpath.get(response_json, "persons/bill2/salary/2025-03")

    # Assert
    assert response.status_code == client.OK
    assert income_tax_1 == 0
    assert income_tax_2 == 750
    assert income_tax_3 == 1500
    assert salary_1 == 0
    assert salary_2 == 4250
    assert salary_3 == 8500


def test_axes_group(test_client) -> None:
    # Arrange
    simulation_json = json.dumps(
        {
            "persons": {
                "bill": {
                    "pension": {"2025-03": 5000},
                },
                "bob": {
                    "capital_returns": {"2025-03": 1000},
                },
            },
            "households": {
                "b&b": {
                    "adults": ["bill", "bob"],
                    "disposable_income": {"2025-03": None},
                    "total_taxes": {"2025-03": None},
                    "total_benefits": {"2025-03": None},
                },
            },
            "axes": [
                [
                    {
                        "count": 3,
                        "name": "salary",
                        "min": 0,
                        "max": 10000,
                        "period": "2025-03",
                    },
                ]
            ],
        },
    )

    # Act
    response = post_json(test_client, simulation_json)
    response_json = json.loads(response.data.decode("utf-8"))
    income_1 = dpath.get(response_json, "households/b&b0/disposable_income/2025-03")
    income_2 = dpath.get(response_json, "households/b&b1/disposable_income/2025-03")
    income_3 = dpath.get(response_json, "households/b&b2/disposable_income/2025-03")
    taxes_1 = dpath.get(response_json, "households/b&b0/total_taxes/2025-03")
    taxes_2 = dpath.get(response_json, "households/b&b1/total_taxes/2025-03")
    taxes_3 = dpath.get(response_json, "households/b&b2/total_taxes/2025-03")
    benefits_1 = dpath.get(response_json, "households/b&b0/total_benefits/2025-03")
    benefits_2 = dpath.get(response_json, "households/b&b1/total_benefits/2025-03")
    benefits_3 = dpath.get(response_json, "households/b&b2/total_benefits/2025-03")

    # Assert
    assert response.status_code == client.OK
    assert income_1 == 6283.3335
    assert income_2 == 10433.333
    assert income_3 == 14423.333
    assert taxes_1 == 916.6667
    assert taxes_2 == 1766.6666
    assert taxes_3 == 2776.6667
    assert benefits_1 == 1200
    assert benefits_2 == 1200
    assert benefits_3 == 1200


def test_axes_group_targeting_individuals(test_client) -> None:
    # Arrange
    simulation_json = json.dumps(
        {
            "persons": {
                "bill": {
                    "pension": {"2025-03": 5000},
                    "salary": {"2025-03": None},
                },
                "bob": {
                    "capital_returns": {"2025-03": 1000},
                },
            },
            "households": {
                "b&b": {
                    "adults": ["bill", "bob"],
                    "disposable_income": {"2025-03": None},
                    "total_taxes": {"2025-03": None},
                    "total_benefits": {"2025-03": None},
                },
            },
            "axes": [
                [
                    {
                        "count": 3,
                        "name": "salary",
                        "min": 0,
                        "max": 10000,
                        "period": "2025-03",
                    },
                ]
            ],
        },
    )

    # Act
    response = post_json(test_client, simulation_json)
    response_json = json.loads(response.data.decode("utf-8"))
    income_1 = dpath.get(response_json, "households/b&b0/disposable_income/2025-03")
    income_2 = dpath.get(response_json, "households/b&b1/disposable_income/2025-03")
    income_3 = dpath.get(response_json, "households/b&b2/disposable_income/2025-03")
    taxes_1 = dpath.get(response_json, "households/b&b0/total_taxes/2025-03")
    taxes_2 = dpath.get(response_json, "households/b&b1/total_taxes/2025-03")
    taxes_3 = dpath.get(response_json, "households/b&b2/total_taxes/2025-03")
    benefits_1 = dpath.get(response_json, "households/b&b0/total_benefits/2025-03")
    benefits_2 = dpath.get(response_json, "households/b&b1/total_benefits/2025-03")
    benefits_3 = dpath.get(response_json, "households/b&b2/total_benefits/2025-03")
    bill_salary_1 = dpath.get(response_json, "persons/bill0/salary/2025-03")
    bill_salary_2 = dpath.get(response_json, "persons/bill2/salary/2025-03")
    bill_salary_3 = dpath.get(response_json, "persons/bill4/salary/2025-03")
    bob_salary_1 = dpath.get(response_json, "persons/bob1/salary/2025-03")
    bob_salary_2 = dpath.get(response_json, "persons/bob3/salary/2025-03")
    bob_salary_3 = dpath.get(response_json, "persons/bob5/salary/2025-03")

    # Assert
    assert response.status_code == client.OK
    assert income_1 == 6283.3335
    assert income_2 == 10433.333
    assert income_3 == 14423.333
    assert taxes_1 == 916.6667
    assert taxes_2 == 1766.6666
    assert taxes_3 == 2776.6667
    assert benefits_1 == 1200
    assert benefits_2 == 1200
    assert benefits_3 == 1200
    assert bill_salary_1 == 0
    assert bill_salary_2 == 5000
    assert bill_salary_3 == 10000
    assert bob_salary_1 == 0
    assert bob_salary_2 == 0
    assert bob_salary_3 == 0


def test_enums_sending_identifier(test_client) -> None:
    simulation_json = json.dumps(
        {
            "persons": {"bill": {}},
            "households": {
                "_": {
                    "adults": ["bill"],
                    "housing_tax": {"2017": None},
                    "accommodation_size": {"2017-01": 300},
                    "housing_occupancy_status": {"2017-01": "free_lodger"},
                },
            },
        },
    )

    response = post_json(test_client, simulation_json)
    assert response.status_code == client.OK
    response_json = json.loads(response.data.decode("utf-8"))
    assert dpath.get(response_json, "households/_/housing_tax/2017") == 0


def test_enum_output(test_client) -> None:
    simulation_json = json.dumps(
        {
            "persons": {
                "bill": {},
            },
            "households": {
                "_": {
                    "adults": ["bill"],
                    "housing_occupancy_status": {"2017-01": None},
                },
            },
        },
    )

    response = post_json(test_client, simulation_json)
    assert response.status_code == client.OK
    response_json = json.loads(response.data.decode("utf-8"))
    assert (
        dpath.get(response_json, "households/_/housing_occupancy_status/2017-01")
        == "tenant"
    )


def test_enum_wrong_value(test_client) -> None:
    simulation_json = json.dumps(
        {
            "persons": {
                "bill": {},
            },
            "households": {
                "_": {
                    "adults": ["bill"],
                    "housing_occupancy_status": {"2017-01": "Unknown value lodger"},
                },
            },
        },
    )

    response = post_json(test_client, simulation_json)
    assert response.status_code == client.BAD_REQUEST
    response_json = json.loads(response.data.decode("utf-8"))
    message = "Possible values are ['owner', 'tenant', 'free_lodger', 'homeless']"
    text = dpath.get(
        response_json,
        "households/_/housing_occupancy_status/2017-01",
    )
    assert message in text


def test_encoding_variable_value(test_client) -> None:
    simulation_json = json.dumps(
        {
            "persons": {"toto": {}},
            "households": {
                "_": {
                    "housing_occupancy_status": {
                        "2017-07": "Locataire ou sous-locataire d‘un logement loué vide non-HLM",
                    },
                    "parent": [
                        "toto",
                    ],
                },
            },
        },
    )

    # No UnicodeDecodeError
    response = post_json(test_client, simulation_json)
    assert response.status_code == client.BAD_REQUEST, response.data.decode("utf-8")
    response_json = json.loads(response.data.decode("utf-8"))
    message = "'Locataire ou sous-locataire d‘un logement loué vide non-HLM' is not a known value for 'housing_occupancy_status'. Possible values are "
    text = dpath.get(
        response_json,
        "households/_/housing_occupancy_status/2017-07",
    )
    assert message in text


def test_encoding_entity_name(test_client) -> None:
    simulation_json = json.dumps(
        {
            "persons": {"O‘Ryan": {}, "Renée": {}},
            "households": {"_": {"adults": ["O‘Ryan", "Renée"]}},
        },
    )

    # No UnicodeDecodeError
    response = post_json(test_client, simulation_json)
    response_json = json.loads(response.data.decode("utf-8"))

    # In Python 3, there is no encoding issue.
    if response.status_code != client.OK:
        message = "'O‘Ryan' is not a valid ASCII value."
        text = response_json["error"]
        assert message in text


def test_encoding_period_id(test_client) -> None:
    simulation_json = json.dumps(
        {
            "persons": {
                "bill": {"salary": {"2017": 60000}},
                "bell": {"salary": {"2017": 60000}},
            },
            "households": {
                "_": {
                    "adults": ["bill", "bell"],
                    "housing_tax": {"à": 400},
                    "accommodation_size": {"2017-01": 300},
                    "housing_occupancy_status": {"2017-01": "tenant"},
                },
            },
        },
    )

    # No UnicodeDecodeError
    response = post_json(test_client, simulation_json)
    assert response.status_code == client.BAD_REQUEST
    response_json = json.loads(response.data.decode("utf-8"))

    # In Python 3, there is no encoding issue.
    if "Expected a period" not in str(response.data):
        message = "'à' is not a valid ASCII value."
        text = response_json["error"]
        assert message in text


def test_str_variable(test_client) -> None:
    new_couple = copy.deepcopy(couple)
    new_couple["households"]["_"]["postal_code"] = {"2017-01": None}
    simulation_json = json.dumps(new_couple)

    response = test_client.post(
        "/calculate",
        data=simulation_json,
        content_type="application/json",
    )

    assert response.status_code == client.OK


def test_periods(test_client) -> None:
    simulation_json = json.dumps(
        {
            "persons": {"bill": {}},
            "households": {
                "_": {
                    "adults": ["bill"],
                    "housing_tax": {"2017": None},
                    "housing_occupancy_status": {"2017-01": None},
                },
            },
        },
    )

    response = post_json(test_client, simulation_json)
    assert response.status_code == client.OK

    response_json = json.loads(response.data.decode("utf-8"))

    yearly_variable = dpath.get(
        response_json,
        "households/_/housing_tax",
    )  # web api year is an int
    assert yearly_variable == {"2017": 200.0}

    monthly_variable = dpath.get(
        response_json,
        "households/_/housing_occupancy_status",
    )  # web api month is a string
    assert monthly_variable == {"2017-01": "tenant"}


def test_two_periods(test_client) -> None:
    """Test `calculate` on a request with mixed types periods: yearly periods following
    monthly or daily periods to check dpath limitation on numeric keys (yearly periods).
    Made to test the case where we have more than one path with a numeric in it.
    See https://github.com/dpath-maintainers/dpath-python/issues/160 for more information.
    """
    simulation_json = json.dumps(
        {
            "persons": {"bill": {}},
            "households": {
                "_": {
                    "adults": ["bill"],
                    "housing_tax": {"2017": None, "2018": None},
                    "housing_occupancy_status": {"2017-01": None, "2018-01": None},
                },
            },
        },
    )

    response = post_json(test_client, simulation_json)
    assert response.status_code == client.OK

    response_json = json.loads(response.data.decode("utf-8"))

    yearly_variable = dpath.get(
        response_json,
        "households/_/housing_tax",
    )  # web api year is an int
    assert yearly_variable == {"2017": 200.0, "2018": 200.0}

    monthly_variable = dpath.get(
        response_json,
        "households/_/housing_occupancy_status",
    )  # web api month is a string
    assert monthly_variable == {"2017-01": "tenant", "2018-01": "tenant"}


def test_handle_period_mismatch_error(test_client) -> None:
    variable = "housing_tax"
    period = "2017-01"

    simulation_json = json.dumps(
        {
            "persons": {"bill": {}},
            "households": {
                "_": {
                    "adults": ["bill"],
                    variable: {period: 400},
                },
            },
        },
    )

    response = post_json(test_client, simulation_json)
    assert response.status_code == client.BAD_REQUEST

    response_json = json.loads(response.data)

    error = dpath.get(response_json, f"households/_/housing_tax/{period}")
    message = f'Unable to set a value for variable "{variable}" for month-long period "{period}"'
    assert message in error


def test_gracefully_handle_unexpected_errors(test_client) -> None:
    """Context.
    =======

    Whenever an exception is raised by the calculation engine, the API will try
    to handle it and to provide a useful message to the user (4XX). When the
    unexpected happens, if the exception is available it will be forwarded
    and given to the user even in this worst case scenario (500).

    Scenario
    ========

    Calculate the housing tax due by Bill a thousand years ago.

    Expected behaviour
    ==================

    In the `country-template`, Housing Tax is only defined from 2010 onwards.
    The calculation engine should therefore raise an exception `ParameterNotFound`.
    The API is not expecting this, but she should handle the situation nonetheless.
    """
    variable = "housing_tax"
    period = "1234-05-06"

    simulation_json = json.dumps(
        {
            "persons": {
                "bill": {},
            },
            "households": {
                "_": {
                    "adults": ["bill"],
                    variable: {
                        period: None,
                    },
                },
            },
        },
    )

    response = post_json(test_client, simulation_json)
    assert response.status_code == client.INTERNAL_SERVER_ERROR

    error = json.loads(response.data)["error"]
    assert f"Unable to compute variable '{variable}' for period {period}" in error
