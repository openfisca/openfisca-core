from openfisca_core.simulations.simulation_builder import SimulationBuilder
from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_core.entities import build_entity


def test_shortcut_to_containing_entity_provided():
    """
    Tests that, when an entity provides a containing entity,
    the shortcut to that containing entity is provided.
    """
    person_entity = build_entity(
        key="person",
        plural="people",
        label="A person",
        is_person=True,
        )
    family_entity = build_entity(
        key="family",
        plural="families",
        label="A family (all members in the same household)",
        containing_entities=["household"],
        roles=[{
            "key": "member",
            "plural": "members",
            "label": "Member",
            }]
        )
    household_entity = build_entity(
        key="household",
        plural="households",
        label="A household, containing one or more families",
        roles=[{
            "key": "member",
            "plural": "members",
            "label": "Member",
            }]
        )

    entities = [person_entity, family_entity, household_entity]

    system = TaxBenefitSystem(entities)
    simulation = SimulationBuilder().build_from_dict(system, {})
    assert simulation.populations["family"].household.entity.key == "household"


def test_shortcut_to_containing_entity_not_provided():
    """
    Tests that, when an entity doesn't provide a containing
    entity, the shortcut to that containing entity is not provided.
    """
    person_entity = build_entity(
        key="person",
        plural="people",
        label="A person",
        is_person=True,
        )
    family_entity = build_entity(
        key="family",
        plural="families",
        label="A family (all members in the same household)",
        containing_entities=[],
        roles=[{
            "key": "member",
            "plural": "members",
            "label": "Member",
            }]
        )
    household_entity = build_entity(
        key="household",
        plural="households",
        label="A household, containing one or more families",
        roles=[{
            "key": "member",
            "plural": "members",
            "label": "Member",
            }]
        )

    entities = [person_entity, family_entity, household_entity]

    system = TaxBenefitSystem(entities)
    simulation = SimulationBuilder().build_from_dict(system, {})
    try:
        simulation.populations["family"].household
        raise AssertionError()
    except AttributeError:
        pass
