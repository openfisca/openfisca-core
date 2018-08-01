from __future__ import unicode_literals
import numpy as np
from openfisca_core.tools import assert_near

from openfisca_country_template.entities import Household, Person

FIRST_PARENT = Household.FIRST_PARENT
SECOND_PARENT = Household.SECOND_PARENT
CHILD = Household.CHILD


class SimulationMockUp(object):
    persons = None


def get_new_famille():
    simulation = SimulationMockUp()
    famille = Household(simulation)
    simulation.persons = Person(simulation)
    famille.members = simulation.persons
    return famille


def test_role_inference():
    famille = get_new_famille()
    famille.members_legacy_role = np.asarray([0, 1, 2, 3, 4, 0, 2, 3])

    assert (famille.members_role == [FIRST_PARENT, SECOND_PARENT, CHILD, CHILD, CHILD, FIRST_PARENT, CHILD, CHILD]).all()


def test_position_inference():
    famille = get_new_famille()
    famille.members_entity_id = np.asarray([0, 0, 0, 0, 0, 1, 1, 1])
    assert_near(famille.members_position, [0, 1, 2, 3, 4, 0, 1, 2])


def test_position_inference_mixed():
    famille = get_new_famille()
    famille.members_entity_id = np.asarray([0, 0, 1, 1, 0, 2, 1, 0])
    assert_near(famille.members_position, [0, 1, 0, 1, 2, 0, 2, 3])
