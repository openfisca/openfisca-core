from __future__ import unicode_literals, print_function, division, absolute_import
from nose.tools import raises

from openfisca_country_template import CountryTaxBenefitSystem


tbs = CountryTaxBenefitSystem()


def test_extension_not_already_loaded():
    assert tbs.get_variable('local_town_child_allowance') is None


def test_load_extension():
    tbs = CountryTaxBenefitSystem()
    assert tbs.get_variable('local_town_child_allowance') is None

    tbs.load_extension('openfisca_extension_template')

    assert tbs.get_variable('local_town_child_allowance') is not None


def test_access_to_parameters():
    tbs.load_extension('openfisca_extension_template')

    assert tbs.parameters('2016-01').local_town.child_allowance.amount == 100.0
    assert tbs.parameters.local_town.child_allowance.amount('2016-01') == 100.0


@raises(ValueError)
def test_failure_to_load_extension_when_directory_doesnt_exist():
    tbs.load_extension('/this/is/not/a/real/path')
