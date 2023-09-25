from openfisca_core import taxscales

import pytest


def test_abstract_tax_scale():
    with pytest.warns(DeprecationWarning):
        result = taxscales.AbstractRateTaxScale()
        assert isinstance(result, taxscales.AbstractRateTaxScale)
