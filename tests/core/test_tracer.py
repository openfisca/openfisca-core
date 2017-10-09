# -*- coding: utf-8 -*-

from nose.tools import raises

from openfisca_core.tracers import Tracer

tracer = Tracer()


@raises(ValueError)
def test_consistency():
        tracer.record_calculation_start("rsa", "2016-01")
        tracer.record_calculation_end("unkwonn", "2016-01", 100)
