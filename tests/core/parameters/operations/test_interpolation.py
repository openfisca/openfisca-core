def test_parameter_interpolation():
    """
    Test that a parameter with two values can be interpolated.
    """
    from policyengine_core.parameters import ParameterNode

    # Create the parameter

    root = ParameterNode(
        data={
            "a": {
                "description": "Example parameter",
                "values": {
                    "2015-01-01": 1,
                    "2016-01-01": 2,
                },
                "metadata": {"interpolation": {"interval": "month"}},
            }
        }
    )

    from policyengine_core.parameters import interpolate_parameters

    interpolated = interpolate_parameters(root)

    # Interpolate halfway

    assert interpolated.a("2015-07-01") == 1.5
