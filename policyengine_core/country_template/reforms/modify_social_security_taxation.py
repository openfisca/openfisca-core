"""
This file defines a reform.

A reform is a set of modifications to be applied to a reference tax and benefit system to carry out experiments.

See https://openfisca.org/doc/key-concepts/reforms.html
"""

# Import from openfisca-core the Python objects used to code the legislation in OpenFisca
from policyengine_core.parameters import ParameterScaleBracket
from policyengine_core.reforms import Reform


class modify_social_security_taxation(Reform):
    def apply(self):
        """
        Apply reform.

        A reform always defines an `apply` method that builds the reformed tax and benefit system from the reference one.
        See https://openfisca.org/doc/coding-the-legislation/reforms.html#writing-a-reform

        Our reform modifies the `social_security_contribution` parameter, which is a scale.
        This parameter is declared in `parameters/taxes/social_security_contribution.yaml`.

        See https://openfisca.org/doc/coding-the-legislation/legislation_parameters.html
        """
        self.modify_parameters(modifier_function=self.modify_brackets)

    @staticmethod
    def modify_brackets(parameters):
        """
        Social security taxation reform.

        This function takes an argument `parameters` which is a in-memory representation
        of the YAML parameters. It can be modified and must be returned.
        """
        # Access the right parameter node:
        brackets = parameters.taxes.social_security_contribution.brackets

        # Add 0.1 to the rates of the second bracket, keeping the same thresholds:
        for rate in brackets[1].rate.values_list:
            rate.value += 0.1

        # Remove the first bracket:
        del brackets[0]

        # Add a new bracket with a higher tax rate for rich people:
        new_bracket = ParameterScaleBracket(
            "new_bracket",
            data={
                "rate": {"2017-01-01": {"value": 0.4}},
                "threshold": {"2017-01-01": {"value": 40000}},
            },
        )
        brackets.append(new_bracket)

        return parameters
