from pytest import fixture

from openfisca_core.entities import build_entity
from openfisca_core.variables import Variable


@fixture
def entity():
    """Create a martian entity for our variable setters tests."""
    return build_entity(
        key = "martian",
        plural = "martians",
        label = "People from Mars",
        is_person = True,
        )


@fixture
def attributes(entity):
    """
    Example attributes of our variable.

    We need to set them to something as variable attributes are class
    attributes, therefore we have to define them before we create the variable.
    """
    return {
        "value_type": bool,
        "entity": entity,
        "default_value": True,
        "definition_period": "year",
        "label": "My taxes",
        "reference": "https://law.gov.example/my-taxes",
        }


@fixture
def make_variable(attributes):
    """
    Example variable.

    This fixture defines our variable dynamically. We do so because we want to
    test the variable setters, called at the moment the variable is
    instantiated.
    """
    return type("my_taxes", (Variable,), attributes)


def test_variable(make_variable):
    assert make_variable()
