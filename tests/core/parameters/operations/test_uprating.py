def test_parameter_uprating():
    from policyengine_core.parameters import ParameterNode

    # Create the parameter

    root = ParameterNode(
        data={
            "to_be_uprated": {
                "description": "Example parameter",
                "values": {
                    "2015-01-01": 1,
                    "2016-01-01": 2,
                },
                "metadata": {
                    "uprating": {
                        "parameter": "uprater",
                    },
                },
            },
            "uprater": {
                "description": "Uprater",
                "values": {
                    "2015-01-01": 1,
                    "2017-01-01": 2,
                    "2018-01-01": 3,
                },
            },
        }
    )

    from policyengine_core.parameters import uprate_parameters

    interpolated = uprate_parameters(root)

    # Interpolate halfway

    assert interpolated.to_be_uprated("2018-01-01") == 2 * 3


def test_parameter_uprating_with_rounding():
    from policyengine_core.parameters import ParameterNode

    # Create the parameter

    root = ParameterNode(
        data={
            "to_be_uprated": {
                "description": "Example parameter",
                "values": {
                    "2015-01-01": 1,
                    "2016-01-01": 2,
                },
                "metadata": {
                    "uprating": {
                        "parameter": "uprater",
                        "rounding": {
                            "interval": 1,
                            "type": "upwards",
                        },
                    },
                },
            },
            "uprater": {
                "description": "Uprater",
                "values": {
                    "2015-01-01": 1,
                    "2017-01-01": 1,
                    "2018-01-01": 1.75,
                },
            },
        }
    )

    from policyengine_core.parameters import uprate_parameters

    interpolated = uprate_parameters(root)

    # Interpolate halfway

    assert interpolated.to_be_uprated("2018-01-01") == 4


def test_parameter_uprating_with_self():
    from policyengine_core.parameters import ParameterNode

    # Create the parameter

    root = ParameterNode(
        data={
            "to_be_uprated": {
                "description": "Example parameter",
                "values": {
                    "2015-01-01": 1,
                    "2016-01-01": 2,
                },
                "metadata": {
                    "uprating": {
                        "parameter": "self",
                    },
                },
            },
        }
    )

    from policyengine_core.parameters import uprate_parameters

    uprated = uprate_parameters(root)

    # Interpolate halfway

    assert uprated.to_be_uprated("2018-01-01") == 8
