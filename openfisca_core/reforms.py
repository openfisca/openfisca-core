# -*- coding: utf-8 -*-

import copy

from . import legislations
from .taxbenefitsystems import TaxBenefitSystem


class Reform(TaxBenefitSystem):
    name = None

    def __init__(self, baseline):
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

    def modify_legislation_json(self, modifier_function):
        """
        Copy the baseline TaxBenefitSystem legislation_json attribute and return it.
        Used by reforms which need to modify the legislation_json, usually in the build_reform() function.
        Validates the new legislation.
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
