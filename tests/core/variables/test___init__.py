from pytest import fixture, mark, raises

from openfisca_core.entities import build_entity
from openfisca_core.variables import Variable


@fixture
def entity():
    """Create a martian entity for our variable creation tests."""
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
def make_variable():
    """
    Example variable.

    This fixture defines our variable dynamically. We do so because we want to
    test the variable valid values, verified at the moment the variable is
    instantiated.
    """
    def _make_variable(attributes):
        return type("my_taxes", (Variable,), attributes)()

    return _make_variable


def test_variable(make_variable, attributes):
    assert make_variable(attributes)


# Definition periods


@mark.parametrize("definition_period", ["eternity", "year", "month", "day", "week", "weekday"])
def test_variable_with_valid_definition_period(definition_period, make_variable, attributes):
    attributes["definition_period"] = definition_period
    assert make_variable(attributes)


@mark.parametrize("definition_period", ["never", 9000])
def test_variable_with_invalid_definition_period(definition_period, make_variable, attributes):
    with raises(ValueError) as error:
        attributes["definition_period"] = definition_period
        make_variable(attributes)

    assert f"Invalid value '{definition_period}' for attribute 'definition_period'" in str(error.value)


def test_variable_without_definition_period(make_variable, attributes):
    with raises(ValueError) as error:
        attributes["definition_period"] = None
        make_variable(attributes)

    assert "Missing attribute 'definition_period'" in str(error.value)
