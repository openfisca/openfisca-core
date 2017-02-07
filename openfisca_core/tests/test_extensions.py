import pkg_resources
import os

from nose.tools import raises

from openfisca_core.tests.dummy_country import DummyTaxBenefitSystem

openfisca_core_dir = pkg_resources.get_distribution('OpenFisca-Core').location
dummy_extension_path = os.path.join(openfisca_core_dir, 'openfisca_core', 'tests', 'dummy_extension')
tbs = DummyTaxBenefitSystem()


def test_extension_not_already_loaded():
    assert tbs.get_column('paris_logement_famille') is None


def test_load_extension():
    tbs.load_extension(dummy_extension_path)
    assert tbs.get_column('paris_logement_familles') is not None


def test_unload_extensions():
    tbs = DummyTaxBenefitSystem()
    assert tbs.get_column('paris_logement_famille') is None


@raises(IOError)
def test_failure_to_load_extension_when_directory_doesnt_exist():
    tbs.load_extension('/this/is/not/a/real/path')
