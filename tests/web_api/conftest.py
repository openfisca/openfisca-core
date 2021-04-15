from http.client import OK, NOT_FOUND
import pytest
from unittest.mock import patch

from openfisca_core.entities import build_entity
from openfisca_core.parameters import ParameterNode
from openfisca_core.periods import MONTH, ETERNITY
from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_core.variables import Variable


from openfisca_core.entities import build_entity

Household = build_entity(
    key = "household",
    plural = "households",
    label = "All the people in a family or group who live together in the same place.",
    doc = "[REMOVED FOR TEST]",
    roles = [
        {
            "key": "parent",
            "plural": "parents",
            "label": "Parents",
            "max": 2,
            "subroles": ["first_parent", "second_parent"],
            "doc": "The one or two adults in charge of the household.",
            },
        {
            "key": "child",
            "plural": "children",
            "label": "Child",
            "doc": "Other individuals living in the household.",
            },
        ],
    )

Person = build_entity(
    key = "person",
    plural = "persons",
    label = "An individual. The minimal legal entity on which a legislation might be applied.",
    doc = "[REMOVED FOR TEST]",
    is_person = True,
    )

@pytest.fixture(scope="package")
def entities():
    return [Household, Person]


@pytest.fixture(scope="package")
def test_tax_benefit_system(entities):
    tax_benefit_system = TaxBenefitSystem(entities)

    # At least one ParameterNode must be defined, or else `openfisca_web_api.app.create_app()` will fail
    tax_benefit_system.parameters = ParameterNode(name="mockParameterNode", 
                                                  data={'amount': {'values': {
                                                                    "2015-01-01": {'value': 550},
                                                                    "2016-01-01": {'value': 600}
                                                                 }}
                                                        })
    
    # At least one Variable must be defined, or else `openfisca_web_api.app.create_app()` will fail
    class initial_variable(Variable):
        value_type = float
        entity = Person
        definition_period = MONTH
        label = "Basic income provided to adults"
        reference = "https://law.gov.example/basic_income"  # Always use the most official source

    tax_benefit_system.add_variable(initial_variable)

    return tax_benefit_system