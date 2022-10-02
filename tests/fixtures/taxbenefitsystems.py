import pytest

from policyengine_core.country_template import CountryTaxBenefitSystem


@pytest.fixture(scope="module")
def tax_benefit_system():
    return CountryTaxBenefitSystem()


@pytest.fixture
def isolated_tax_benefit_system():
    return CountryTaxBenefitSystem()
