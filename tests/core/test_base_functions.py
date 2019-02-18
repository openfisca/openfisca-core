import numpy as np
from openfisca_core.tools import assert_near

from openfisca_country_template.situation_examples import single
from openfisca_country_template.entities import Person
from openfisca_core.model_api import *  # noqa
from openfisca_core.simulations import Simulation
from openfisca_core.periods import period

from .test_countries import tax_benefit_system
from .test_holders import force_storage_on_disk


class state_variable(Variable):
    entity = Person
    definition_period = MONTH
    base_function = requested_period_last_value
    value_type = int


tax_benefit_system.add_variable(state_variable)


def get_simulation(**kwargs):
    return Simulation(tax_benefit_system = tax_benefit_system, simulation_json = single, **kwargs)


def test_memory_cache():
    simulation = get_simulation()
    value = np.asarray([1])
    simulation.person.get_holder('state_variable').put_in_cache(value, period('2017-01'))
    assert_near(
        simulation.calculate('state_variable', '2017-02'),
        value
        )


def test_disk_cache():
    simulation = get_simulation(memory_config = force_storage_on_disk)
    value = np.asarray([1])
    simulation.person.get_holder('state_variable').put_in_cache(value, period('2017-01'))
    assert_near(
        simulation.calculate('state_variable', '2017-02'),
        value
        )
