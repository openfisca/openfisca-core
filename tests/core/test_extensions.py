from nose.tools import raises

from openfisca_country_template import CountryTaxBenefitSystem


original_tbs = CountryTaxBenefitSystem()


def test_load_extension():
    tbs = original_tbs.clone()
    assert tbs.get_variable('local_town_child_allowance') is None

    tbs.load_extension('openfisca_extension_template')

    assert tbs.get_variable('local_town_child_allowance') is not None
    assert original_tbs.get_variable('local_town_child_allowance') is None


def test_access_to_parameters():
    tbs = original_tbs.clone()
    tbs.load_extension('openfisca_extension_template')

    assert tbs.parameters('2016-01').local_town.child_allowance.amount == 100.0
    assert tbs.parameters.local_town.child_allowance.amount('2016-01') == 100.0


@raises(ValueError)
def test_failure_to_load_extension_when_directory_doesnt_exist():
    original_tbs.load_extension('/this/is/not/a/real/path')
