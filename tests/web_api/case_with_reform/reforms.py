from openfisca_core.model_api import Variable, Reform, MONTH
from openfisca_country_template.entities import Person


def test_dynamic_variable():
    class NewDynamicClass(Variable):
        value_type = bool
        default_value = True
        entity = Person
        label = "The person goes to school (only relevant for children)"
        definition_period = MONTH

    NewDynamicClass.__name__ = "goes_to_school"
    return NewDynamicClass


class add_variable_reform(Reform):
    def apply(self):
        self.add_variable(test_dynamic_variable())
