# -*- coding: utf-8 -*-

import numpy as np
import pytest

from openfisca_core.tracers import FullTracer, TracingParameterNodeAtInstant
from openfisca_core.tools import assert_near

from openfisca_country_template.variables.housing import HousingOccupancyStatus
from .parameters_fancy_indexing.test_fancy_indexing import parameters

@pytest.fixture
def tracer():
    return FullTracer()


def test_variable_stats(tracer):
    tracer.enter_calculation("A", 2017)
    tracer.enter_calculation("B", 2017)
    tracer.enter_calculation("B", 2017)
    tracer.enter_calculation("B", 2016)

    assert tracer.get_nb_requests('B') == 3
    assert tracer.get_nb_requests('A') == 1
    assert tracer.get_nb_requests('C') == 0


def test_log_format(tracer):
    tracer.enter_calculation("A", 2017)
    tracer.enter_calculation("B", 2017)
    tracer.record_calculation_result(1)
    tracer.exit_calculation()
    tracer.record_calculation_result(2)
    tracer.exit_calculation()

    lines = tracer.computation_log()
    assert lines[0] == '  A<2017> >> [2]'
    assert lines[1] == '    B<2017> >> [1]'


def test_no_wrapping():
    tracer = Tracer()
    tracer.record_calculation_start("A", 2017)
    tracer.record_calculation_end("A", 2017, HousingOccupancyStatus.encode(np.repeat('tenant', 100)))

    lines = tracer.computation_log()
    assert "'tenant'" in lines[0]
    assert "\n" not in lines[0]


def test_trace_enums(tracer):
    tracer.enter_calculation("A", 2017)
    tracer.record_calculation_result(HousingOccupancyStatus.encode(np.array(['tenant'])))
    tracer.exit_calculation()

    lines = tracer.computation_log()
    assert lines[0] == "  A<2017> >> ['tenant']"


#  Tests on tracing with fancy indexing
zone = np.asarray(['z1', 'z2', 'z2', 'z1'])
housing_occupancy_status = np.asarray(['owner', 'owner', 'tenant', 'tenant'])
family_status = np.asarray(['single', 'couple', 'single', 'couple'])


def check_tracing_params(accessor, param_key):
    tracer = FullTracer()
    tracer.enter_calculation('A', '2015-01')
    tracingParams = TracingParameterNodeAtInstant(parameters('2015-01-01'), tracer)
    param = accessor(tracingParams)
    assert tracer.trees[0]['parameters'][0]['name'] == param_key


@pytest.mark.parametrize("test", [
    (lambda P: P.rate.single.owner.z1, 'rate.single.owner.z1'),  # basic case
    (lambda P: P.rate.single.owner[zone], 'rate.single.owner'),  # fancy indexing on leaf
    (lambda P: P.rate.single[housing_occupancy_status].z1, 'rate.single'),  # on a node
    (lambda P: P.rate.single[housing_occupancy_status][zone], 'rate.single'),  # double fancy indexing
    (lambda P: P.rate[family_status][housing_occupancy_status].z2, 'rate'),  # double + node
    (lambda P: P.rate[family_status][housing_occupancy_status][zone], 'rate'),  # triple
    ])
def test_parameters(test):
    check_tracing_params(*test)
