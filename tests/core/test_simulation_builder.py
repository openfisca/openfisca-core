from openfisca_core.simulation_builder import SimulationBuilder
from .test_countries import tax_benefit_system
from yaml import load

def test_simulation():
  input_yaml = """
    salary:
      2016-10: 12000
  """

  simulation = SimulationBuilder(tax_benefit_system).build_from_dict(load(input_yaml))

  assert 12000 == simulation.get_array("salary", "2016-10")
