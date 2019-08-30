from openfisca_core.entities import build_entity
from openfisca_core.model_api import *
from openfisca_core.taxbenefitsystems import TaxBenefitSystem

# ENTITIES

Household = build_entity(
    key = "household",
    plural = "households",
    roles = [
        {
            'key': 'parent',
            'plural': 'parents',
            'label': u'Parents',
            'max': 2,
            'subroles': ['first_parent', 'second_parent'],
            },
        {
            'key': 'child',
            'plural': 'children',
            'label': u'Child',
            }
        ]
    )

Person = build_entity(
    key = "person",
    plural = "persons",
    is_person = True,
    )

entities = [Household, Person]

# VARIABLES

class root(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH

    def formula(person, period, parameters):
      return person("income_a", period) - person("tax_a", period)


class income_a(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH

    def formula(person, period, parameters):
      return 42.2


class tax_a(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH

    def formula(person, period, parameters):
      return 21.1

# TAXBENEFITSYSTEM

class TestTaxBenefitSystem(TaxBenefitSystem):
    def __init__(self):
        # We initialize our tax and benefit system with the general constructor
        super(TestTaxBenefitSystem, self).__init__(entities)

        # We add to our tax and benefit system all the variables
        self.add_variables([root, income_a, tax_a])

        # We add to our tax and benefit system all the legislation parameters defined in the  parameters files
        # param_path = os.path.join(COUNTRY_DIR, 'parameters')
        # self.load_parameters(param_path)
