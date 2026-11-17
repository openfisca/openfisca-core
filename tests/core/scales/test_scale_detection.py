from openfisca_core.parameters import (
    ParameterScale,
)


def test_empty_scale() -> None:
    parameter_data = {
        "brackets": [],
    }
    scale = ParameterScale("root", data=parameter_data, file_path=None)
    assert scale._type == "marginal_rate"


# def test_scale_detection():
#     scale = ParameterNode(
#         "root",
#         data={
#             "scale": {
#                 "brackets": [
#                     {
#                         "threshold": {"values": {"2010-01-01": 0}},
#                         "rate": {"values": {"2010-01-01": 0.1}},
# #                        "amount": {"values": {"2010-01-01": 5, "2020-01-01": None}},
#                     },
#                     {
#                         "threshold": {"values": {"2010-01-01": 100}},
#                         "rate": {"values": {"2010-01-01": 0.2}},
# #                        "amount": {"values": {"2010-01-01": 7, "2020-01-01": None}},
#                     },
#                 ]
#             }
#         },
#     )("2024-01-01").scale
#     print(type(scale).__name__, scale.calc([50.0, 200.0]))
#     assert_near(scale.calc([50.0, 200.0]), [5, 30])
