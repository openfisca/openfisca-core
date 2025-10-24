import numpy

from openfisca_core import taxscales


def test_threshold_from_tax_base() -> None:
    tax_base = numpy.array([0, 33_000, 500, 400_000])
    tax_scale = taxscales.LinearAverageRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(400, 0.1)
    tax_scale.add_bracket(15_000, 0.4)
    tax_scale.add_bracket(200_000, 0.6)

    result = tax_scale.threshold_from_tax_base(tax_base)

    assert isinstance(result, numpy.ndarray)
    assert (result == numpy.array([0, 15_000, 400, 200_000])).all()
