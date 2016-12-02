import numpy as np
from openfisca_core.tools import assert_near

from dummy_country import Famille, Individu

DEMANDEUR = Famille.DEMANDEUR
CONJOINT = Famille.CONJOINT
ENFANT = Famille.ENFANT


class SimulationMockUp(object):
    persons = None


def get_new_famille():
    simulation = SimulationMockUp()
    famille = Famille(simulation)
    simulation.persons = Individu(simulation)
    famille.members = simulation.persons
    return famille


def test_role_inference():
    famille = get_new_famille()
    famille.members_legacy_role = np.asarray([0, 1, 2, 3, 4, 0, 2, 3])

    assert (famille.members_role == [DEMANDEUR, CONJOINT, ENFANT, ENFANT, ENFANT, DEMANDEUR, ENFANT, ENFANT]).all()


def test_position_inference():
    famille = get_new_famille()
    famille.members_entity_id = np.asarray([0, 0, 0, 0, 0, 1, 1, 1])
    assert_near(famille.members_position, [0, 1, 2, 3, 4, 0, 1, 2])


def test_position_inference_mixed():
    famille = get_new_famille()
    famille.members_entity_id = np.asarray([0, 0, 1, 1, 0, 2, 1, 0])
    assert_near(famille.members_position, [0, 1, 0, 1, 2, 0, 2, 3])
