import pytest

from openfisca_core import taxscales


def test_abstract_tax_scale() -> None:
    with pytest.warns(DeprecationWarning):
        result = taxscales.AbstractRateTaxScale()
        assert isinstance(result, taxscales.AbstractRateTaxScale)
