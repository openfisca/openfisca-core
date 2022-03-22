def test_tax_scale_descendants_are_complete():
    """Tests that calling the `get_descendant` function of a ParameterScale returns the rates and thresholds as Parameters.
    """

    from openfisca_core.parameters import ParameterNode, Parameter

    parameters = ParameterNode("parameters", data={
        "root_node": {
            "first_child": {
                "scale_parameter": {
                    "brackets": [
                        {
                            "rate": {
                                "2022-01-01": 0.1,
                                },
                            "threshold": {
                                "2022-01-01": 0,
                                }
                            },
                        {
                            "rate": {
                                "2022-01-01": 0.2,
                                },
                            "threshold": {
                                "2022-01-01": 100,
                                }
                            }
                        ]
                    },
                "normal_parameter": {
                    "2022-01-01": 5
                    }
                }
            }
        })

    # Get descendants which are parameters (ignore nodes)
    parameter_descendants = list(filter(lambda p: isinstance(p, Parameter), parameters.get_descendants()))

    # Check that the expected names are in the descendants
    parameter_names = list(map(lambda p: p.name, parameter_descendants))
    assert all(name in parameter_names for name in [
        "parameters.root_node.first_child.scale_parameter[0].rate",
        "parameters.root_node.first_child.scale_parameter[0].threshold",
        "parameters.root_node.first_child.scale_parameter[1].rate",
        "parameters.root_node.first_child.scale_parameter[1].threshold",
        ]), "ParameterScale descendants don't include bracket thresholds and rates"
