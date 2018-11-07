from __future__ import unicode_literals, print_function, division, absolute_import
from nose.tools import raises

from openfisca_core.parameters import ParameterNode
from openfisca_country_template import CountryTaxBenefitSystem


tbs = CountryTaxBenefitSystem()


def test_extension_not_already_loaded():
    assert tbs.get_variable('local_town_child_allowance') is None


def walk_and_count(node):
    c = 0
    for item_name, item in node.children.items():
        if isinstance(item, ParameterNode):
            c += walk_and_count(item)
        else:
            c += 1
    return c


def test_load_extension():
    country_template_variables_number = 16
    country_template_parameters_number = 8
    assert len(tbs.variables) == country_template_variables_number
    assert walk_and_count(tbs.parameters) == country_template_parameters_number

    # Access a parameter of the country template > OK
    assert tbs.parameters('2016-01').benefits.housing_allowance == 0.25
    assert tbs.parameters.benefits.housing_allowance('2016-01') == 0.25
    assert tbs.parameters.benefits.housing_allowance is not None

    tbs.load_extension('openfisca_extension_template')

    # Access a variable of the extension template > OK
    assert len(tbs.variables) == country_template_variables_number + 1
    assert tbs.get_variable('local_town_child_allowance') is not None

    # Access a parameter of the extension template > KO, sometimes
    assert walk_and_count(tbs.parameters) == country_template_parameters_number + 1
    assert tbs.parameters('2016-01').local_town.child_allowance.amount == 100.0
    assert tbs.parameters.local_town.child_allowance.amount('2016-01') == 100.0
    assert tbs.parameters.local_town.child_allowance.amount is not None


def test_unload_extensions():
    tbs = CountryTaxBenefitSystem()
    assert tbs.get_variable('local_town_child_allowance') is None


@raises(ValueError)
def test_failure_to_load_extension_when_directory_doesnt_exist():
    tbs.load_extension('/this/is/not/a/real/path')
