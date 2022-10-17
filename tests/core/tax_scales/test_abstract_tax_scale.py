import pytest

from policyengine_core import taxscales


def test_abstract_tax_scale():
    with pytest.warns(DeprecationWarning):
        result = taxscales.AbstractTaxScale()
        assert type(result) == taxscales.AbstractTaxScale
