import pytest

from openfisca_web_api import app


@pytest.fixture(scope="module")
def test_client(tax_benefit_system):
    """This module-scoped fixture creates an API client for the TBS defined in the `tax_benefit_system`
        fixture. This `tax_benefit_system` is mutable, so you can add/update variables.

    Example:

        .. code-block:: python

            from policyengine_core.country_template import entities
            from policyengine_core import periods
            from policyengine_core.variables import Variable
            ...

            class new_variable(Variable):
                value_type = float
                entity = entities.Person
                definition_period = periods.MONTH
                label = "New variable"
                reference = "https://law.gov.example/new_variable"  # Always use the most official source

            tax_benefit_system.add_variable(new_variable)
            flask_app = app.create_app(tax_benefit_system)

    """

    # Create the test API client
    flask_app = app.create_app(tax_benefit_system)
    return flask_app.test_client()
