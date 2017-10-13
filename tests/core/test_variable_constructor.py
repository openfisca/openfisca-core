# -*- coding: utf-8 -*-

from nose.tools import assert_equal, raises

from openfisca_core.model_api import *  # noqa analysis:ignore
from openfisca_country_template.entities import *  # noqa analysis:ignore

def test_ok():
    attributes = {'column': BoolCol, 'entity':  Household, 'definition_period': MONTH}
    variable = Variable('variale_name', attributes)

@raises(ValueError)
def test_wrong_entity_type():
    attributes = {'column': BoolCol, 'entity':  'Household', 'definition_period': MONTH}
    variable = Variable('variale_name', attributes)
