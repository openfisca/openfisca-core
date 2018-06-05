"""
This files tests the performance of the test runner (openfisca-run-test).
It uses the existing tests from openfisca-france because it is the largest set we currently have.
"""

import os
import time
import pkg_resources

from openfisca_core.tools.test_runner import run_tests
from openfisca_france import CountryTaxBenefitSystem

start_time = time.time()
tbs = CountryTaxBenefitSystem()
time_spent = time.time() - start_time
print("Generate Tax Benefit System: --- {}s seconds ---".format(time_spent))

start_time = time.time()
openfisca_france_dir = pkg_resources.get_distribution('OpenFisca-France').location
yaml_tests_dir = os.path.join(openfisca_france_dir, 'tests', 'mes-aides.gouv.fr')
time_spent = time.time() - start_time

start_time = time.time()
run_tests(tbs, yaml_tests_dir)
time_spent = time.time() - start_time
print("Pass Mes-aides tests: --- {}s seconds ---".format(time_spent))
