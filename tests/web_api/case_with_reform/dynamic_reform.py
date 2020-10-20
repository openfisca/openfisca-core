"""
This file defines a dynamic reform based on input data.

See https://openfisca.org/doc/key-concepts/reforms.html
"""

from openfisca_core.periods import MONTH
from openfisca_core.reforms import Reform
from openfisca_core.variables import Variable

from openfisca_country_template.entities import Person


def create_dynamic_variable(
        name,
        value_type,
        entity,
        default_value,
        definition_period,
        label,
        reference,
        ):
    """Create new variable dynamically."""

    NewVariable = type(name, (Variable,), {
        "__module__": "tests.web_api.case_with_reform.dynamic_reform",
        "value_type": value_type,
        "entity": entity,
        "default_value": default_value,
        "definition_period": definition_period,
        "label": label,
        "reference": reference,
        })

    return NewVariable


class add_dynamic_variable(Reform):
    def apply(self):
        """
        Apply reform.

        See https://openfisca.org/doc/coding-the-legislation/reforms.html#writing-a-reform
        """
        NewVariable = create_dynamic_variable(
            name = "goes_to_school",
            value_type = bool,
            entity = Person,
            default_value = True,
            definition_period = MONTH,
            label = "The person goes to school (only relevant for children)",
            reference = "https://law.gov.example/goes_to_school",
            )

        self.add_variable(NewVariable)
