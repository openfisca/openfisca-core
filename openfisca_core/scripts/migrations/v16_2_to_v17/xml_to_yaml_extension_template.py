"""xml_to_yaml_extension_template.py : Parse XML parameter files for Extension-Template and convert them to YAML files. Comments are NOT transformed.

Usage :
  `python xml_to_yaml_extension_template.py output_dir`
or just (output is written in a directory called `yaml_parameters`):
  `python xml_to_yaml_extension_template.py`
"""

import os
import sys

import openfisca_extension_template

from . import xml_to_yaml

target_path = sys.argv[1] if len(sys.argv) > 1 else "yaml_parameters"

param_dir = os.path.dirname(openfisca_extension_template.__file__)
param_files = [
    "parameters.xml",
]
legislation_xml_info_list = [
    (os.path.join(param_dir, param_file), []) for param_file in param_files
]

xml_to_yaml.write_parameters(legislation_xml_info_list, target_path)
