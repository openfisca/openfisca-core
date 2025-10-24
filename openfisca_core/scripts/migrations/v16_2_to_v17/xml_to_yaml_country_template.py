"""xml_to_yaml_country_template.py : Parse XML parameter files for Country-Template and convert them to YAML files. Comments are NOT transformed.

Usage :
  `python xml_to_yaml_country_template.py output_dir`
or just (output is written in a directory called `yaml_parameters`):
  `python xml_to_yaml_country_template.py`
"""

import os
import sys

from openfisca_country_template import COUNTRY_DIR, CountryTaxBenefitSystem

from . import xml_to_yaml

tax_benefit_system = CountryTaxBenefitSystem()

target_path = sys.argv[1] if len(sys.argv) > 1 else "yaml_parameters"

param_dir = os.path.join(COUNTRY_DIR, "parameters")
param_files = [
    "benefits.xml",
    "general.xml",
    "taxes.xml",
]
legislation_xml_info_list = [
    (os.path.join(param_dir, param_file), []) for param_file in param_files
]

xml_to_yaml.write_parameters(legislation_xml_info_list, target_path)
