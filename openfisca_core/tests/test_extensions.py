from os import path

from nose.tools import raises

from openfisca_core.tests.dummy_country import DummyTaxBenefitSystem, TEST_DIRECTORY


dummy_extension_path = path.join(TEST_DIRECTORY, 'dummy_extension')
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
