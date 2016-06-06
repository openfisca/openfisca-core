from nose.tools import raises

from openfisca_core.tests.dummy_country import init_tax_benefit_system

tbs = init_tax_benefit_system()


def test_extension_not_already_loaded():
    assert tbs.get_column('paris_logement_famille') is None


def test_load_extension():
    tbs.load_extension('https://github.com/sgmap/openfisca-paris.git')
    assert tbs.get_column('paris_logement_familles') is not None


def test_unload_extensions():
    tbs = init_tax_benefit_system()
    assert tbs.get_column('paris_logement_famille') is None


@raises(IOError)
def test_failure_to_load_extension_when_directory_doesnt_exist():
    tbs.load_extension('/this/is/not/a/real/path')
