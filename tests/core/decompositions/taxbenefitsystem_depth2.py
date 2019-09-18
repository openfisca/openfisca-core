from openfisca_core.entities import build_entity
from openfisca_core.model_api import *
from openfisca_core.taxbenefitsystems import TaxBenefitSystem

# ENTITIES

Person = build_entity(
    key = "person",
    plural = "persons",
    label = 'An individual. The minimal legal entity on which a legislation might be applied.',
    is_person = True,
    )

entities = [Person]

# VARIABLES

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


class tax_b(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH

    def formula(person, period, parameters):
      return 13


# INTERMEDIATE VARIABLES CORRESPONDING TO DECOMPOSITION NODES

class root(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH

    def formula(person, period, parameters):
      return person("income_a", period) - person("taxes", period)


class taxes(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH

    def formula(person, period, parameters):
      return person("tax_a", period) + person("tax_b", period)


# TAXBENEFITSYSTEM

class TaxBenefitSystemFixture(TaxBenefitSystem):
    def __init__(self):
        # We initialize our tax and benefit system with the general constructor
        super(TaxBenefitSystemFixture, self).__init__(entities)

        # We add to our tax and benefit system all the variables
        self.add_variables(root, income_a, taxes, tax_a, tax_b)

        # We add to our tax and benefit system all the legislation parameters defined in the  parameters files
        # param_path = os.path.join(COUNTRY_DIR, 'parameters')
        # self.load_parameters(param_path)
