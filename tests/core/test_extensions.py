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
    assert len(tbs.variables) == 16
    assert walk_and_count(tbs.parameters) == 8
    tbs.load_extension('openfisca_extension_template')
    
    assert len(tbs.variables) == 17
    assert tbs.get_variable('local_town_child_allowance') is not None

    assert walk_and_count(tbs.parameters) == 9
    assert tbs.parameters.local_town.child_allowance.amount is not None
    


def test_unload_extensions():
    tbs = CountryTaxBenefitSystem()
    assert tbs.get_variable('local_town_child_allowance') is None


@raises(ValueError)
def test_failure_to_load_extension_when_directory_doesnt_exist():
    tbs.load_extension('/this/is/not/a/real/path')
