"""Pytest plugin for running OpenFisca tests in parallel worker processes.

This plugin is loaded by pytest workers spawned by run_tests_in_parallel().
It configures each worker with its own tax-benefit system and test options.

The parallel test architecture works as follows:
1. Main process: run_tests_in_parallel() splits test files into batches
2. Main process: spawns multiple pytest workers via subprocess
3. Each worker: loads this plugin to configure its test environment
4. Each worker: runs its batch of tests independently
5. Main process: aggregates results and reports failures

Configuration is passed via environment variables:
- OPENFISCA_COUNTRY_PACKAGE: The country package to load
- OPENFISCA_EXTENSIONS: JSON array of extensions to load
- OPENFISCA_REFORMS: JSON array of reforms to apply
- OPENFISCA_OPTIONS: JSON object with test options (verbose, name_filter, etc.)
"""

import json
import os

from openfisca_core.scripts import build_tax_benefit_system
from openfisca_core.tools.test_runner import OpenFiscaPlugin


def pytest_configure(config):
    """Pytest hook called when each worker process initializes.

    This function is automatically invoked by pytest when it loads this plugin.
    It sets up the OpenFisca test environment for the worker by:
    1. Reading configuration from environment variables
    2. Building the tax-benefit system with specified country, extensions, and reforms
    3. Registering the OpenFisca plugin with pytest

    Args:
        config: Pytest config object provided by pytest framework
    """
    # Extract country package from environment (optional)
    country = os.environ.get("OPENFISCA_COUNTRY_PACKAGE") or None

    # Parse JSON arrays for extensions and reforms
    extensions = json.loads(os.environ.get("OPENFISCA_EXTENSIONS", "[]"))
    reforms = json.loads(os.environ.get("OPENFISCA_REFORMS", "[]"))

    # Build the tax-benefit system with the specified configuration
    tbs = build_tax_benefit_system(country, extensions, reforms)

    # Parse test options (verbose, name_filter, etc.)
    options_json = os.environ.get("OPENFISCA_OPTIONS", "{}")
    options = json.loads(options_json)

    # Create and register the OpenFisca plugin for this worker
    plugin = OpenFiscaPlugin(tbs, options)
    config.pluginmanager.register(plugin, name="openfisca_parallel_plugin")
