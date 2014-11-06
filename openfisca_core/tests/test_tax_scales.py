# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
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

from nose.tools import assert_equal, assert_less
import numpy as np


from openfisca_core.taxscales import MarginalRateTaxScale


def test_linear_average_rate_tax_scale():
    marginal_tax_scale = MarginalRateTaxScale()
    marginal_tax_scale.add_bracket(0, 0)
    marginal_tax_scale.add_bracket(1, .1)
    marginal_tax_scale.add_bracket(2, .2)
    base = np.array([1, 1.5, 2, 2.5])
    assert_equal(
        max(abs(marginal_tax_scale.calc(base) - np.array([0, .05, .1, .2]))),
        0,
        "MarginalRateTaxScale computation error"
        )
    average_tax_scale = marginal_tax_scale.to_average()
    assert_equal(
        max(abs(np.array(average_tax_scale.rates) - np.array([0, 0, .05, .2]))),
        0,
        "MarginalRateTaxScale computation error"
        )
    assert_equal(
        max(abs(np.array(average_tax_scale.thresholds) - np.array([0, 1, 2, float('Inf')]))),
        0,
        "MarginalRateTaxScale to LinearAverageTaxScale conversion error"
        )
    error_margin = 1e-10
    assert_less(
        max(abs(np.array(average_tax_scale.calc(base)) - np.array([0, .0375, .1, .125]))),
        error_margin,
        "LinearAverageTaxScale  computation error"
        )
    new_marginal_tax_scale = average_tax_scale.to_marginal()
    assert (new_marginal_tax_scale.rates == marginal_tax_scale.rates), \
        "LinearAverageTaxScale to MarginalRateTaxScale conversion error"
    assert (new_marginal_tax_scale.thresholds == marginal_tax_scale.thresholds), \
        "LinearAverageTaxScale to MarginalRateTaxScale conversion error"


if __name__ == '__main__':
    import logging
    import sys
    logging.basicConfig(level = logging.ERROR, stream = sys.stdout)
    test_linear_average_rate_tax_scale()
