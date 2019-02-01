from openfisca_core.tools.test_runner import _run_test

import pytest

class TaxBenefitSystem:
	def __init__(self):
		self.variables = {}

class Simulation:
	def __init__(self):
		self.tax_benefit_system = TaxBenefitSystem()
		self.entities = {}
	def get_entity(self, plural = None):
		return None

def test_variable_not_found():
	test = {"output": {"unknown_variable": 0}}	
	with pytest.raises(ValueError):
		_run_test(Simulation(), test)
