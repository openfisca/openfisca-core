import numpy

from openfisca_core import taxscales


def test_rate_from_bracket_indice():
    tax_base = numpy.array([0, 1_000, 1_500, 50_000])
    tax_scale = taxscales.MarginalRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(400, 0.1)
    tax_scale.add_bracket(15_000, 0.4)

    bracket_indice = tax_scale.bracket_indices(tax_base)
    result = tax_scale.rate_from_bracket_indice(bracket_indice)

    assert isinstance(result, numpy.ndarray)
    assert (result == numpy.array([0., 0.1, 0.1, 0.4])).all()

