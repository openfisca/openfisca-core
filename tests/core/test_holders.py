# -*- coding: utf-8 -*-

import numpy as np
from nose.tools import assert_equal

from openfisca_country_template.situation_examples import couple
from openfisca_core.simulations import Simulation
from openfisca_core.periods import period as make_period
from test_countries import tax_benefit_system


def test_set_input_enum():
    simulation = Simulation(tax_benefit_system = tax_benefit_system, simulation_json = couple)
    status_occupancy = np.asarray(['owner'])
    period = make_period('2017-12')
    HousingOccupancyStatus = tax_benefit_system.get_variable('housing_occupancy_status').possible_values
    simulation.household.get_holder('housing_occupancy_status').set_input(period, status_occupancy)
    result = simulation.calculate('housing_occupancy_status', period)
    assert_equal(result, HousingOccupancyStatus.owner)
