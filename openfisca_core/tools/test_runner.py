from __future__ import annotations

from typing import Optional, Sequence, Union
from openfisca_core.types import TaxBenefitSystemType, OptionsSchema

import pytest

# For backwards compatibility.
from openfisca_core.simulation_builder import SimulationBuilder  # noqa: F401

# For backwards compatibility.
from openfisca_core.errors import SituationParsingError, VariableNotFound  # noqa: F401

# For backwards compatibility.
from openfisca_core.warnings import LibYAMLWarning  # noqa: F401

# For backwards compatibility.
from ._asserts import assert_near  # noqa: F401

# For backwards compatibility.
from ._misc import _get_tax_benefit_system  # noqa: F401

# For backwards compatibility.
from ._yaml import yaml, Loader  # noqa: F401

# For backwards compatibility.
from ._yaml_file import YamlFile  # noqa: F401

# For backwards compatibility.
from ._yaml_item import YamlItem  # noqa: F401

# For backwards compatibility.
from ._yaml_plugin import YamlPlugin as OpenFiscaPlugin


def run_tests(
        tax_benefit_system: TaxBenefitSystemType,
        paths: Sequence[str],
        options: Optional[OptionsSchema] = None,
        ) -> Union[int, pytest.ExitCode]:
    """
    Runs all the YAML tests contained in a file or a directory.

    If `path` is a directory, subdirectories will be recursively explored.

    :param .TaxBenefitSystem tax_benefit_system: the tax-benefit system to use to run the tests
    :param str or list paths: A path, or a list of paths, towards the files or directories containing the tests to run. If a path is a directory, subdirectories will be recursively explored.
    :param dict options: See more details below.

    :raises :exc:`AssertionError`: if a test does not pass

    :return: the number of sucessful tests excecuted

    **Testing options**:

    +-------------------------------+-----------+-------------------------------------------+
    | Key                           | Type      | Role                                      |
    +===============================+===========+===========================================+
    | verbose                       | ``bool``  |                                           |
    +-------------------------------+-----------+ See :any:`openfisca_test` options doc     |
    | name_filter                   | ``str``   |                                           |
    +-------------------------------+-----------+-------------------------------------------+

    """

    argv = []

    if options is None:
        options = {}

    if "pdb" in options and options["pdb"]:
        argv.append('--pdb')

    if "verbose" in options and options["verbose"]:
        argv.append('--verbose')

    if isinstance(paths, str):
        paths = [paths]

    return pytest.main([*argv, *paths] if True else paths, plugins = [OpenFiscaPlugin(tax_benefit_system, options)])
