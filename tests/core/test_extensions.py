import pytest


def test_load_extension(tax_benefit_system):
    tbs = tax_benefit_system.clone()
    assert tbs.get_variable("local_town_child_allowance") is None

    tbs.load_extension("openfisca_extension_template")

    assert tbs.get_variable("local_town_child_allowance") is not None
    assert tax_benefit_system.get_variable("local_town_child_allowance") is None


def test_access_to_parameters(tax_benefit_system):
    tbs = tax_benefit_system.clone()
    tbs.load_extension("openfisca_extension_template")

    assert tbs.parameters("2016-01").local_town.child_allowance.amount == 100.0
    assert tbs.parameters.local_town.child_allowance.amount("2016-01") == 100.0


def test_failure_to_load_extension_when_directory_doesnt_exist(tax_benefit_system):
    with pytest.raises(ValueError):
        tax_benefit_system.load_extension("/this/is/not/a/real/path")
