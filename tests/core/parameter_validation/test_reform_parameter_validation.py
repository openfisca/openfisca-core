import pytest

from openfisca_core.parameters import ParameterNode
from openfisca_core.reforms import Reform


def test_modify_parameters_must_return_parameter_node(tax_benefit_system):
    """Test that modify_parameters raises ValueError when modifier function doesn't return ParameterNode."""

    def modifier_function_without_return(parameters):
        """A modifier function that doesn't return anything (returns None)."""
        parameters.benefits.basic_income.update(start="2015-01-01", value=100)
        # Missing return statement - this should raise ValueError

    def modifier_function_returns_wrong_type(parameters):
        """A modifier function that returns the wrong type."""
        parameters.benefits.basic_income.update(start="2015-01-01", value=100)
        return "not a ParameterNode"  # Wrong return type

    def modifier_function_returns_none_explicitly(parameters):
        """A modifier function that explicitly returns None."""
        parameters.benefits.basic_income.update(start="2015-01-01", value=100)
        return None

    def modifier_function_correct(parameters):
        """A modifier function that correctly returns ParameterNode."""
        parameters.benefits.basic_income.update(start="2015-01-01", value=100)
        return parameters

    # Test case 1: Function without return statement (implicitly returns None)
    class ReformWithoutReturn(Reform):
        def apply(self):
            self.modify_parameters(modifier_function=modifier_function_without_return)

    with pytest.raises(ValueError) as exc_info:
        ReformWithoutReturn(tax_benefit_system)

    assert "modifier_function_without_return" in str(exc_info.value)
    assert "must return a ParameterNode" in str(exc_info.value)

    # Test case 2: Function returns wrong type
    class ReformWithWrongReturnType(Reform):
        def apply(self):
            self.modify_parameters(
                modifier_function=modifier_function_returns_wrong_type
            )

    with pytest.raises(ValueError) as exc_info:
        ReformWithWrongReturnType(tax_benefit_system)

    assert "modifier_function_returns_wrong_type" in str(exc_info.value)
    assert "must return a ParameterNode" in str(exc_info.value)

    # Test case 3: Function explicitly returns None
    class ReformWithExplicitNone(Reform):
        def apply(self):
            self.modify_parameters(
                modifier_function=modifier_function_returns_none_explicitly
            )

    with pytest.raises(ValueError) as exc_info:
        ReformWithExplicitNone(tax_benefit_system)

    assert "modifier_function_returns_none_explicitly" in str(exc_info.value)
    assert "must return a ParameterNode" in str(exc_info.value)

    # Test case 4: Correct function that returns ParameterNode (should work)
    class ReformCorrect(Reform):
        def apply(self):
            self.modify_parameters(modifier_function=modifier_function_correct)

    # This should not raise any exception
    reformed_tbs = ReformCorrect(tax_benefit_system)

    # Verify the reform was applied correctly
    assert reformed_tbs.parameters.benefits.basic_income("2015-01-01") == 100


def test_modify_parameters_error_message_includes_function_details(tax_benefit_system):
    """Test that the error message includes the function name and module."""

    def my_faulty_modifier(parameters):
        return "wrong type"

    class TestReform(Reform):
        def apply(self):
            self.modify_parameters(modifier_function=my_faulty_modifier)

    with pytest.raises(ValueError) as exc_info:
        TestReform(tax_benefit_system)

    error_message = str(exc_info.value)
    assert "my_faulty_modifier" in error_message
    assert (
        "__main__" in error_message
        or "test_reform_parameter_validation" in error_message
    )
    assert "must return a ParameterNode" in error_message


def test_modify_parameters_with_lambda_function(tax_benefit_system):
    """Test that the error message works correctly even with lambda functions."""

    class TestReform(Reform):
        def apply(self):
            # Using a lambda that doesn't return ParameterNode
            self.modify_parameters(modifier_function=lambda params: None)

    with pytest.raises(ValueError) as exc_info:
        TestReform(tax_benefit_system)

    error_message = str(exc_info.value)
    assert "<lambda>" in error_message
    assert "must return a ParameterNode" in error_message


def test_modify_parameters_preserves_parameter_structure(tax_benefit_system):
    """Test that a correctly implemented modifier function preserves parameter structure."""

    def correct_modifier(parameters):
        # Create a copy to avoid modifying the original
        import copy

        modified_params = copy.deepcopy(parameters)
        modified_params.benefits.basic_income.update(start="2015-01-01", value=200)
        return modified_params

    class TestReform(Reform):
        def apply(self):
            self.modify_parameters(modifier_function=correct_modifier)

    reformed_tbs = TestReform(tax_benefit_system)

    # Verify the parameter structure is preserved and modification applied
    assert isinstance(reformed_tbs.parameters, ParameterNode)
    assert reformed_tbs.parameters.benefits.basic_income("2015-01-01") == 200

    # Verify that the original tax benefit system is not modified
    original_value = tax_benefit_system.parameters.benefits.basic_income("2015-01-01")
    assert original_value != 200  # Should be the original value
