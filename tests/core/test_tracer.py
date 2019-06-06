# -*- coding: utf-8 -*-

import numpy as np
import pytest

from openfisca_core.tracers import Tracer, TracingParameterNodeAtInstant
from openfisca_core.tools import assert_near

from openfisca_country_template.variables.housing import HousingOccupancyStatus
from .parameters_fancy_indexing.test_fancy_indexing import parameters


def test_consistency():
    with pytest.raises(ValueError):
        tracer = Tracer()
        tracer.record_calculation_start("rsa", 2017)
        tracer.record_calculation_end("unkwonn", 2017, 100)


def test_variable_stats():
    tracer = Tracer()
    tracer.record_calculation_start("A", 2017)
    tracer.record_calculation_start("B", 2017)
    tracer.record_calculation_start("B", 2017)
    tracer.record_calculation_start("B", 2016)

    assert tracer.usage_stats['B']['nb_requests'] == 3
    assert tracer.usage_stats['A']['nb_requests'] == 1
    assert tracer.usage_stats['C']['nb_requests'] == 0


def test_log_format():
    tracer = Tracer()
    tracer.record_calculation_start("A", 2017)
    tracer.record_calculation_start("B", 2017)
    tracer.record_calculation_end("B", 2017, np.array([1]))
    tracer.record_calculation_end("A", 2017, np.array([2]))

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


def test_trace_enums():
    tracer = Tracer()
    tracer.record_calculation_start("A", 2017)
    tracer.record_calculation_end("A", 2017, HousingOccupancyStatus.encode(np.array(['tenant'])))

    lines = tracer.computation_log()
    assert lines[0] == "  A<2017> >> ['tenant']"


#  Tests on tracing with fancy indexing
zone = np.asarray(['z1', 'z2', 'z2', 'z1'])
housing_occupancy_status = np.asarray(['owner', 'owner', 'tenant', 'tenant'])
family_status = np.asarray(['single', 'couple', 'single', 'couple'])


def check_tracing_params(accessor, param_key):
    tracer = Tracer()
    tracer.record_calculation_start('A', '2015-01')
    tracingParams = TracingParameterNodeAtInstant(parameters('2015-01-01'), tracer)
    param = accessor(tracingParams)
    assert_near(tracer.trace['A<2015-01>']['parameters'][param_key], param)


@pytest.mark.parametrize("test", [
    (lambda P: P.rate.single.owner.z1, 'rate.single.owner.z1<2015-01-01>'),  # basic case
    (lambda P: P.rate.single.owner[zone], 'rate.single.owner<2015-01-01>'),  # fancy indexing on leaf
    (lambda P: P.rate.single[housing_occupancy_status].z1, 'rate.single<2015-01-01>'),  # on a node
    (lambda P: P.rate.single[housing_occupancy_status][zone], 'rate.single<2015-01-01>'),  # double fancy indexing
    (lambda P: P.rate[family_status][housing_occupancy_status].z2, 'rate<2015-01-01>'),  # double + node
    (lambda P: P.rate[family_status][housing_occupancy_status][zone], 'rate<2015-01-01>'),  # triple
    ])
def test_parameters(test):
    check_tracing_params(*test)
