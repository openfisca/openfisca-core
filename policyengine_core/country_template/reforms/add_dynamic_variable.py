"""
This file defines a reform to add a dynamic variable, based on input data.

A reform is a set of modifications to be applied to a reference tax and benefit system to carry out experiments.

See https://openfisca.org/doc/key-concepts/reforms.html
"""

# Import the Entities specifically defined for this tax and benefit system
from policyengine_core.country_template.entities import Person

# Import from openfisca-core the Python objects used to code the legislation in OpenFisca
from policyengine_core.periods import MONTH
from policyengine_core.reforms import Reform
from policyengine_core.variables import Variable


def create_dynamic_variable(name, **variable):
    """Create new variable dynamically."""
    NewVariable = type(
        name,
        (Variable,),
        {
            "value_type": variable["value_type"],
            "entity": variable["entity"],
            "default_value": variable["default_value"],
            "definition_period": variable["definition_period"],
            "label": variable["label"],
            "reference": variable["reference"],
        },
    )

    return NewVariable


class add_dynamic_variable(Reform):
    def apply(self):
        """
        Apply reform.

        A reform always defines an `apply` method that builds the reformed tax
        and benefit system from the reference one.

        See https://openfisca.org/doc/coding-the-legislation/reforms.html#writing-a-reform
        """
        NewVariable = create_dynamic_variable(
            name="goes_to_school",
            value_type=bool,
            entity=Person,
            default_value=True,
            definition_period=MONTH,
            label="The person goes to school (only relevant for children)",
            reference="https://law.gov.example/goes_to_school",
        )

        self.add_variable(NewVariable)
