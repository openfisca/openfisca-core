from openfisca_core.parameters import (
    ParameterScale,
)

def test_empty_scale() -> None:
    parameter_data = {
        "brackets": [],
    }
    scale = ParameterScale("root", data=parameter_data, file_path=None)
    assert scale._type == "marginal_rate"
