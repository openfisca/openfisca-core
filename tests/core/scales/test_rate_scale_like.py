import numpy

from openfisca_core import scales


def test_threshold_from_base() -> None:
    base = numpy.array([0, 33_000, 500, 400_000])
    scale = scales.AverageRateScale()
    scale.add_bracket(0, 0)
    scale.add_bracket(400, 0.1)
    scale.add_bracket(15_000, 0.4)
    scale.add_bracket(200_000, 0.6)

    result = scale.threshold_from_base(base)

    assert isinstance(result, numpy.ndarray)
    assert (result == numpy.array([0, 15_000, 400, 200_000])).all()
