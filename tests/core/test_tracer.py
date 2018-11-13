# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
from nose.tools import raises, assert_equals
import numpy as np

from openfisca_core.tracers import Tracer, TracingParameterNodeAtInstant
from openfisca_core.tools import assert_near

from .parameters_fancy_indexing.test_fancy_indexing import parameters


@raises(ValueError)
def test_consistency():
    tracer = Tracer()
    tracer.record_calculation_start("rsa", 2017)
    tracer.record_calculation_end("unkwonn", 2017, 100)


def test_variable_stats():
    tracer = Tracer()
    tracer.record_calculation_start("A", 2017)
    tracer.record_calculation_start("B", 2017)
    tracer.record_calculation_start("B", 2017)
    tracer.record_calculation_start("B", 2016)

    assert_equals(tracer.usage_stats['B']['nb_requests'], 3)
    assert_equals(tracer.usage_stats['A']['nb_requests'], 1)
    assert_equals(tracer.usage_stats['C']['nb_requests'], 0)


#  Tests on tracing with fancy indexing
zone = np.asarray(['z1', 'z2', 'z2', 'z1'])
housing_occupancy_status = np.asarray(['owner', 'owner', 'tenant', 'tenant'])
family_status = np.asarray(['single', 'couple', 'single', 'couple'])


def test_parameters_fancy_indexing():
    tracer = Tracer()
    tracer.record_calculation_start('A', '2015-01')
    tracingParams = TracingParameterNodeAtInstant(parameters('2015-01-01'), tracer)
    param = tracingParams.rate.single.owner[zone]
    assert_near(tracer.trace['A<2015-01>']['parameters']['rate.single.owner<2015-01-01>'], param)


def test_parameters_fancy_indexing_node():
    tracer = Tracer()
    tracer.record_calculation_start('A', '2015-01')
    tracingParams = TracingParameterNodeAtInstant(parameters('2015-01-01'), tracer)
    param = tracingParams.rate.single[housing_occupancy_status].z1
    assert_near(tracer.trace['A<2015-01>']['parameters']['rate.single<2015-01-01>'], param)


def test_parameters_fancy_indexing_double():
    tracer = Tracer()
    tracer.record_calculation_start('A', '2015-01')
    tracingParams = TracingParameterNodeAtInstant(parameters('2015-01-01'), tracer)
    param = tracingParams.rate.single[housing_occupancy_status][zone]
    assert_near(tracer.trace['A<2015-01>']['parameters']['rate.single<2015-01-01>'], param)


def test_parameters_fancy_indexing_double_with_node():
    tracer = Tracer()
    tracer.record_calculation_start('A', '2015-01')
    tracingParams = TracingParameterNodeAtInstant(parameters('2015-01-01'), tracer)
    param = tracingParams.rate[family_status][housing_occupancy_status].z2
    assert_near(tracer.trace['A<2015-01>']['parameters']['rate<2015-01-01>'], param)
