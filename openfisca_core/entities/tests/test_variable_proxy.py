import pytest

from openfisca_core.entities import Entity
from openfisca_core.errors import VariableNotFoundError
from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_core.variables import Variable

from .._variable_proxy import VariableProxy


@pytest.fixture()
def variables():
    """A variable descriptor."""

    return VariableProxy()


@pytest.fixture
def entity():
    """An entity."""

    return Entity("", "individuals", "", "")


@pytest.fixture
def ThisVar(entity):
    """A variable."""

    return type(
        "ThisVar",
        (Variable,),
        {
            "definition_period": "month",
            "value_type": float,
            "entity": entity,
            },
        )


@pytest.fixture
def ThatVar():
    """Another variable."""

    class ThatVar(Variable):
        definition_period = "month"
        value_type = float
        entity = Entity("", "martians", "", "")

    return ThatVar


@pytest.fixture
def tbs(entity, ThisVar, ThatVar):
    """A tax-benefit system."""

    tbs = TaxBenefitSystem([entity])
    tbs.add_variable(ThisVar)
    tbs.add_variable(ThatVar)
    return tbs


def test_variables_without_variable_name(variables):
    """Raises a TypeError when called without ``variable_name``."""

    with pytest.raises(TypeError, match = "'variable_name'"):
        variables.get()


def test_variables_without_owner(variables):
    """Returns NotImplemented when called without an ``owner``."""

    assert variables.get("ThisVar") == NotImplemented


def test_variables_setter(entity):
    """Raises AttributeError when tryng to set ``variables``."""

    with pytest.raises(AttributeError, match = "can't set attribute"):
        entity.variables = object()


def test_variables_without_tax_benefit_system(entity):
    """Returns None when called without a TaxBenefitSystem."""

    assert not entity.variables


def test_variables_when_exists(entity, tbs, ThisVar):
    """Returns the variable when it exists."""

    entity.tax_benefit_system = tbs
    variable = entity.variables.get("ThisVar")
    assert isinstance(variable, ThisVar)


def test_variables_when_doesnt_exist(entity, tbs):
    """Returns None when it does not."""

    entity.tax_benefit_system = tbs
    assert not entity.variables.get("OtherVar")


def test_variables_when_exists_and_check_exists(entity, tbs, ThisVar):
    """Raises a VariableNotFoundError when checking for existance."""

    entity.tax_benefit_system = tbs
    variable = entity.variables.exists().get("ThisVar")
    assert isinstance(variable, ThisVar)


def test_variables_when_doesnt_exist_and_check_exists(entity, tbs):
    """Raises a VariableNotFoundError when checking for existance."""

    entity.tax_benefit_system = tbs

    with pytest.raises(VariableNotFoundError, match = "'OtherVar'"):
        entity.variables.exists().get("OtherVar")


def test_variables_when_exists_and_defined_for(entity, tbs, ThisVar):
    """Returns the variable when it exists and defined for the entity."""

    entity.tax_benefit_system = tbs
    variable = entity.variables.isdefined().get("ThisVar")
    assert isinstance(variable, ThisVar)


def test_variables_when_exists_and_not_defined_for(entity, tbs):
    """Raises a ValueError when it exists but defined for another var."""

    entity.tax_benefit_system = tbs

    with pytest.raises(ValueError, match = "'martians'"):
        entity.variables.isdefined().get("ThatVar")


def test_variables_when_doesnt_exist_and_check_defined_for(entity, tbs):
    """Raises a VariableNotFoundError when it doesn't exist."""

    entity.tax_benefit_system = tbs

    with pytest.raises(VariableNotFoundError, match = "'OtherVar'"):
        entity.variables.isdefined().get("OtherVar")


def test_variables_composition(entity, tbs):
    """Conditions can be composed."""

    entity.tax_benefit_system = tbs

    assert entity.variables.exists().isdefined().get("ThisVar")


def test_variables_permutation(entity, tbs):
    """Conditions can be permuted."""

    entity.tax_benefit_system = tbs

    assert entity.variables.isdefined().exists().get("ThisVar")
