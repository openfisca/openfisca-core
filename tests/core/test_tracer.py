# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from nose.tools import raises, assert_equals

from openfisca_core.tracers import Tracer


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
