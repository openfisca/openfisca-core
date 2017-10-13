# -*- coding: utf-8 -*-

from nose.tools import assert_equal, raises

from openfisca_core.model_api import *  # noqa analysis:ignore
from openfisca_country_template.entities import *  # noqa analysis:ignore


def test():

    class rsa(Variable):
        entity = Household
        definition_period = MONTH
        column = FloatCol

    variable = rsa()


@raises(ValueError)
def test_wrong_entity_type():

    class rsa(Variable):
        entity = 'Household'
        definition_period = MONTH
        column = FloatCol

    variable = rsa()
