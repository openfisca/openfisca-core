import os
import json
from openfisca_core.scripts import build_tax_benefit_system
from openfisca_core.tools.test_runner import OpenFiscaPlugin

# pytest hook

def pytest_configure(config):
    country = os.environ.get("OPENFISCA_COUNTRY_PACKAGE") or None
    extensions = json.loads(os.environ.get("OPENFISCA_EXTENSIONS", "[]"))
    reforms = json.loads(os.environ.get("OPENFISCA_REFORMS", "[]"))
    tbs = build_tax_benefit_system(country, extensions, reforms)

    options_json = os.environ.get("OPENFISCA_OPTIONS", "{}")
    options = json.loads(options_json)

    plugin = OpenFiscaPlugin(tbs, options)
    config.pluginmanager.register(plugin, name="openfisca_parallel_plugin")
