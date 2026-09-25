from openfisca_country_template.entities import entities

from openfisca_core.legislationstructure.legislation_structure import (
    LegislationStructure,
)


def test_links() -> None:
    structure = LegislationStructure(entities)
    assert structure
