from nose.tools import raises

from openfisca_country_template import CountryTaxBenefitSystem

tbs = CountryTaxBenefitSystem()


def test_extension_not_already_loaded():
    assert tbs.get_variable('local_town_child_allowance') is None


def test_load_extension():
    tbs.load_extension('openfisca_extension_template')
    assert tbs.get_variable('local_town_child_allowance') is not None


def test_unload_extensions():
    tbs = CountryTaxBenefitSystem()
    assert tbs.get_variable('local_town_child_allowance') is None


@raises(ValueError)
def test_failure_to_load_extension_when_directory_doesnt_exist():
    tbs.load_extension('/this/is/not/a/real/path')
