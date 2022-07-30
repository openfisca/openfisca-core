# -*- coding: utf-8 -*-


import pytest

from openfisca_core.periods import YEAR, MONTH, DAY, period


@pytest.mark.parametrize("test", [
    (period('year:2014:2'), YEAR, 2, period('2014'), period('2015')),
    (period(2017), MONTH, 12, period('2017-01'), period('2017-12')),
    (period('year:2014:2'), MONTH, 24, period('2014-01'), period('2015-12')),
    (period('month:2014-03:3'), MONTH, 3, period('2014-03'), period('2014-05')),
    (period(2017), DAY, 365, period('2017-01-01'), period('2017-12-31')),
    (period('year:2014:2'), DAY, 730, period('2014-01-01'), period('2015-12-31')),
    (period('month:2014-03:3'), DAY, 92, period('2014-03-01'), period('2014-05-31')),
    ])
def test_subperiods(test):

    def check_subperiods(period, unit, length, first, last):
        subperiods = period.get_subperiods(unit)
        assert len(subperiods) == length
        assert subperiods[0] == first
        assert subperiods[-1] == last

        check_subperiods(*test)
