from openfisca_core.parameters import Scale
from openfisca_web_api.loader.parameters import build_api_parameter, build_api_scale


def test_build_rate_scale() -> None:
    """Extracts a 'rate' children from a bracket collection."""
    data = {
        "brackets": [
            {
                "rate": {"2014-01-01": {"value": 0.5}},
                "threshold": {"2014-01-01": {"value": 1}},
            },
        ],
    }
    rate = Scale("this rate", data, None)
    assert build_api_scale(rate, "rate") == {"2014-01-01": {1: 0.5}}


def test_build_amount_scale() -> None:
    """Extracts an 'amount' children from a bracket collection."""
    data = {
        "brackets": [
            {
                "amount": {"2014-01-01": {"value": 0}},
                "threshold": {"2014-01-01": {"value": 1}},
            },
        ],
    }
    rate = Scale("that amount", data, None)
    assert build_api_scale(rate, "amount") == {"2014-01-01": {1: 0}}


def test_full_rate_scale() -> None:
    """Serializes a 'rate' scale parameter."""
    data = {
        "brackets": [
            {
                "rate": {"2014-01-01": {"value": 0.5}},
                "threshold": {"2014-01-01": {"value": 1}},
            },
        ],
    }
    scale = Scale("rate", data, None)
    api_scale = build_api_parameter(scale, {})
    assert api_scale == {
        "description": None,
        "id": "rate",
        "metadata": {},
        "brackets": {"2014-01-01": {1: 0.5}},
    }


def test_walk_node_amount_scale() -> None:
    """Serializes an 'amount' scale parameter."""
    data = {
        "brackets": [
            {
                "amount": {"2014-01-01": {"value": 0}},
                "threshold": {"2014-01-01": {"value": 1}},
            },
        ],
    }
    scale = Scale("amount", data, None)
    api_scale = build_api_parameter(scale, {})
    assert api_scale == {
        "description": None,
        "id": "amount",
        "metadata": {},
        "brackets": {"2014-01-01": {1: 0}},
    }
