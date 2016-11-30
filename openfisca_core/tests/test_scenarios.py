import numpy as np
from openfisca_core.tools import assert_near

from dummy_country import Famille, Individu

DEMANDEUR = Famille.DEMANDEUR
CONJOINT = Famille.CONJOINT
ENFANT = Famille.ENFANT


class SimulationMockUp(object):
    persons = None


simulation = SimulationMockUp()
famille = Famille(simulation)
simulation.persons = Individu(simulation)
famille.members = simulation.persons


def test_role_inference():
    famille.members_legacy_role = np.asarray([0, 1, 2, 3, 4, 0, 2, 3])

    assert (famille.members_role == [DEMANDEUR, CONJOINT, ENFANT, ENFANT, ENFANT, DEMANDEUR, ENFANT, ENFANT]).all()


def test_position_inference():
    famille.members_entity_id = np.asarray([0, 0, 0, 0, 0, 1, 1, 1])
    assert_near(famille.members_position, [0, 1, 2, 3, 4, 0, 1, 2])
