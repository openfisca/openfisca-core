import os
from typing import Dict, Type
from policyengine_core.data.dataset import Dataset
from policyengine_core.populations.population import Population
from policyengine_core.taxbenefitsystems import TaxBenefitSystem
from policyengine_core.country_template import entities
from policyengine_core.country_template.situation_examples import couple
from policyengine_core.simulations import Simulation as CoreSimulation
from policyengine_core.simulations import (
    Microsimulation as CoreMicrosimulation,
)
from policyengine_core.country_template.data.datasets.country_template_dataset import (
    CountryTemplateDataset,
)
from pathlib import Path
import logging
from .constants import COUNTRY_DIR

DATASETS = [CountryTemplateDataset]  # Important: must be instantiated


class CountryTaxBenefitSystem(TaxBenefitSystem):
    entities = entities.entities
    variables_dir = COUNTRY_DIR / "variables"
    parameters_dir = COUNTRY_DIR / "parameters"
    auto_carry_over_input_variables = False


class Simulation(CoreSimulation):
    default_tax_benefit_system = CountryTaxBenefitSystem


class Microsimulation(CoreMicrosimulation):
    default_tax_benefit_system = CountryTaxBenefitSystem
    default_dataset = CountryTemplateDataset
    default_dataset_year = 2022


if 2022 not in CountryTemplateDataset.years:
    logging.warn("Default country template dataset not found. Building it.")
    CountryTemplateDataset.generate(2022)
