# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


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
