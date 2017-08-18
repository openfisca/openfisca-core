# -*- coding: utf-8 -*-

import copy

from . import legislations
from .taxbenefitsystems import TaxBenefitSystem


class Reform(TaxBenefitSystem):
    """A modified TaxBenefitSystem

    In OpenFisca, a reform is a modified TaxBenefitSystem. It can add or replace variables and call `self.modify_legislation()` to modify the parameters of the legislation. All reforms must subclass `Reform` and implement a math `apply()`. Such a function can add or replace variables and call `self.modify_legislation()` to modify the parameters of the legislation.

    Example:

    >>> from openfisca_core import reforms, legislations
    >>>
    >>> def modify_my_legislation(legislation):
    >>>     # Add new parameters
    >>>     new_params = legislations.load_file(name='reform_name', file_path='path_to_yaml_file.yaml')
    >>>     legislation.add_child('reform_name', new_params)
    >>>
    >>>     # Update a value
    >>>     legislation.taxes.some_tax.some_param.update(period=some_period, value=1000.0)
    >>>
    >>>    return legislation
    >>>
    >>> class MyReform(reforms.Reform):
    >>>    def apply(self):
    >>>        self.add_variable(some_variable)
    >>>        self.update_variable(some_other_variable)
    >>>        self.modify_legislation(modifier_function=modify_my_legislation)
    """
    name = None

    def __init__(self, baseline):
        """
        :param baseline: Baseline TaxBenefitSystem.
        """
        self.baseline = baseline
        self._legislation = baseline.get_legislation()
        self.legislation_at_instant_cache = baseline.legislation_at_instant_cache
        self.column_by_name = baseline.column_by_name.copy()
        self.decomposition_file_path = baseline.decomposition_file_path
        self.Scenario = baseline.Scenario
        self.key = unicode(self.__class__.__name__)
        if not hasattr(self, 'apply'):
            raise Exception("Reform {} must define an `apply` function".format(self.key))
        self.apply()

    def __getattr__(self, attribute):
        return getattr(self.baseline, attribute)

    @property
    def full_key(self):
        key = self.key
        assert key is not None, 'key was not set for reform {} (name: {!r})'.format(self, self.name)
        if self.baseline is not None and hasattr(self.baseline, 'key'):
            baseline_full_key = self.baseline.full_key
            key = u'.'.join([baseline_full_key, key])
        return key

    def modify_legislation(self, modifier_function):
        """
        Make modifications on the parameters of the legislation

        Call this function in `apply()` if the reform asks for legislation parameter modifications.

        :param modifier_function: A function that takes an object of type `openfisca_core.legislations.Node` and should return an object of the same type.
        """
        baseline_legislation = self.baseline.get_legislation()
        baseline_legislation_copy = copy.deepcopy(baseline_legislation)
        reform_legislation = modifier_function(baseline_legislation_copy)
        assert reform_legislation is not None, \
            'modifier_function {} in module {} must return the modified legislation'.format(
                modifier_function.__name__,
                modifier_function.__module__,
                )
        assert isinstance(reform_legislation, legislations.Node)
        self._legislation = reform_legislation
        self.legislation_at_instant_cache = {}
