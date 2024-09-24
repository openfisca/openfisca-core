from __future__ import annotations

import copy

from openfisca_core.parameters import ParameterNode
from openfisca_core.taxbenefitsystems import TaxBenefitSystem


class Reform(TaxBenefitSystem):
    """A modified TaxBenefitSystem.

    All reforms must subclass `Reform` and implement a method `apply()`.

    In this method, the reform can add or replace variables and call `modify_parameters` to modify the parameters of the legislation.

    Example:
        >>> from openfisca_core import reforms
        >>> from openfisca_core.parameters import load_parameter_file
        >>>
        >>> def modify_my_parameters(parameters):
        >>> # Add new parameters
        >>>     new_parameters = load_parameter_file(name='reform_name', file_path='path_to_yaml_file.yaml')
        >>>     parameters.add_child('reform_name', new_parameters)
        >>>
        >>> # Update a value
        >>>     parameters.taxes.some_tax.some_param.update(period=some_period, value=1000.0)
        >>>
        >>>    return parameters
        >>>
        >>> class MyReform(reforms.Reform):
        >>>    def apply(self):
        >>>        self.add_variable(some_variable)
        >>>        self.update_variable(some_other_variable)
        >>>        self.modify_parameters(modifier_function = modify_my_parameters)

    """

    name = None

    def __init__(self, baseline) -> None:
        """:param baseline: Baseline TaxBenefitSystem."""
        super().__init__(baseline.entities)
        self.baseline = baseline
        self.parameters = baseline.parameters
        self._parameters_at_instant_cache = baseline._parameters_at_instant_cache
        self.variables = baseline.variables.copy()
        self.decomposition_file_path = baseline.decomposition_file_path
        self.key = self.__class__.__name__
        if not hasattr(self, "apply"):
            msg = f"Reform {self.key} must define an `apply` function"
            raise Exception(msg)
        self.apply()

    def __getattr__(self, attribute):
        return getattr(self.baseline, attribute)

    @property
    def full_key(self):
        key = self.key
        assert (
            key is not None
        ), f"key was not set for reform {self} (name: {self.name!r})"
        if self.baseline is not None and hasattr(self.baseline, "key"):
            baseline_full_key = self.baseline.full_key
            key = f"{baseline_full_key}.{key}"
        return key

    def modify_parameters(self, modifier_function):
        """Make modifications on the parameters of the legislation.

        Call this function in `apply()` if the reform asks for legislation parameter modifications.

        Args:
            modifier_function: A function that takes a :obj:`.ParameterNode` and should return an object of the same type.

        """
        baseline_parameters = self.baseline.parameters
        baseline_parameters_copy = copy.deepcopy(baseline_parameters)
        reform_parameters = modifier_function(baseline_parameters_copy)
        if not isinstance(reform_parameters, ParameterNode):
            return ValueError(
                f"modifier_function {modifier_function.__name__} in module {modifier_function.__module__} must return a ParameterNode",
            )
        self.parameters = reform_parameters
        self._parameters_at_instant_cache = {}
        return None
