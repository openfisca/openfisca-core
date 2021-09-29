import pytest

from openfisca_core.commons import Dummy


def test_dummy_deprecation():
    """Dummy throws a deprecation warning when instantiated."""

    with pytest.warns(DeprecationWarning):
        assert Dummy()
