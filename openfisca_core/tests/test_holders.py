# -*- coding: utf-8 -*-


import numpy

from . import test_countries


def test_new_test_case_array():
    axis_count = 3
    axis_max = 100000
    axis_min = 0
    simulation = test_countries.tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            dict(
                count = axis_count,
                name = 'salaire_brut',
                max = axis_max,
                min = axis_min,
                ),
            ],
        period = 2014,
        parent1 = {},
        ).new_simulation(debug = True)
    simulation.calculate('salaire_brut')
    salaire_brut = simulation.get_holder('salaire_brut').new_test_case_array(simulation.period)
    assert (salaire_brut - numpy.linspace(axis_min, axis_max, axis_count) == 0).all(), \
        u'salaire_brut: {}'.format(salaire_brut)
