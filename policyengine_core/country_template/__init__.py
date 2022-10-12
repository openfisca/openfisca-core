import os
from typing import Dict, Type
from policyengine_core.data.dataset import Dataset
from policyengine_core.populations.population import Population
from policyengine_core.taxbenefitsystems import TaxBenefitSystem
from policyengine_core.country_template import entities
from policyengine_core.country_template.situation_examples import couple
from policyengine_core.simulations import Simulation as CoreSimulation
from policyengine_core.simulations import (
    WeightedSimulation as CoreWeightedSimulation,
)
from policyengine_core.country_template.data.datasets.country_template_dataset import (
    CountryTemplateDataset,
)
from pathlib import Path


COUNTRY_DIR = Path(__file__).parent

DATASETS = [CountryTemplateDataset]

# Our country tax and benefit class inherits from the general TaxBenefitSystem class.
# The name CountryTaxBenefitSystem must not be changed, as all tools of the OpenFisca ecosystem expect a CountryTaxBenefitSystem class to be exposed in the __init__ module of a country package.
class CountryTaxBenefitSystem(TaxBenefitSystem):
    def __init__(self):
        # We initialize our tax and benefit system with the general constructor
        super().__init__(entities.entities)

        # We add to our tax and benefit system all the variables
        self.add_variables_from_directory(
            os.path.join(COUNTRY_DIR, "variables")
        )

        # We add to our tax and benefit system all the legislation parameters defined in the  parameters files
        param_path = os.path.join(COUNTRY_DIR, "parameters")
        self.load_parameters(param_path)

        # We define which variable, parameter and simulation example will be used in the OpenAPI specification
        self.open_api_config = {
            "variable_example": "disposable_income",
            "parameter_example": "taxes.income_tax_rate",
            "simulation_example": couple,
        }


class Simulation(CoreSimulation):
    def __init__(
        self,
        *args,
        tax_benefit_system: TaxBenefitSystem = None,
        **kwargs,
    ):
        if tax_benefit_system is None:
            tax_benefit_system = CountryTaxBenefitSystem()

        super().__init__(
            *args,
            tax_benefit_system=tax_benefit_system,
            **kwargs,
        )


class Microsimulation(CoreWeightedSimulation):
    def __init__(
        self,
        *args,
        tax_benefit_system: TaxBenefitSystem = None,
        dataset: Type[Dataset] = None,
        dataset_options: dict = None,
        **kwargs,
    ):
        if tax_benefit_system is None:
            tax_benefit_system = CountryTaxBenefitSystem()

        if dataset is None:
            dataset = CountryTemplateDataset

        dataset_instance = dataset()
        if not dataset_instance.exists(dataset_options):
            # Build the dataset if it doesn't exist. A country package might not want to do this: for example,
            # you might want to throw an exception instead.
            dataset_instance.build(dataset_options)

        super().__init__(
            *args,
            tax_benefit_system=tax_benefit_system,
            dataset=dataset,
            **kwargs,
        )
