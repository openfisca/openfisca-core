import importlib
import os
import traceback
import warnings

import yaml

from openfisca_core.warnings import LibYAMLWarning


def import_country_package(country_package_name):
    """Import a country package."""

    try:
        return importlib.import_module(country_package_name)

    except ImportError as error:
        message = os.linesep.join([
            traceback.format_exc(),
            f"Could not import module `{country_package_name}`. Are you sure",
            "it is installed in your environment? If so, look at the stack",
            "trace above to determine the origin of this error. See more at",
            "<https://github.com/openfisca/country-template#installing>.",
            os.linesep,
            ])

        raise ImportError(message) from error


def import_yaml():
    """Import the yaml library."""

    try:
        return yaml, yaml.__getattribute__("CLoader")

    except AttributeError:
        message = [
            "libyaml is not installed in your environment.",
            "This can make your test suite slower to run. Once you have",
            "installed libyaml, run 'pip uninstall pyyaml && pip install",
            "pyyaml --no-cache-dir' so that it is used in your Python",
            "environment.",
            ]
        warnings.warn(" ".join(message), LibYAMLWarning)
        return yaml, yaml.__getattribute__("SafeLoader")
