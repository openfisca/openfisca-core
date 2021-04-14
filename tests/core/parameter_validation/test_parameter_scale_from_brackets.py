import os
from openfisca_core.parameters import ParameterScale
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
year = 2016


def test_init_from_brackets(tax_benefit_system):
    scale = tax_benefit_system.parameters.taxes.social_security_contribution
    brackets = scale.brackets.copy()

    assert brackets is not scale.brackets

    cloned_scale = ParameterScale(
        name = "clone",
        data = dict(description = "clone"),
        brackets = brackets,
        )
    assert cloned_scale.brackets is not scale.brackets
    assert cloned_scale.brackets == scale.brackets
