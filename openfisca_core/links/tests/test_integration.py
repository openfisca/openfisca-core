"""Tests for Phase 2: entity integration and link resolution."""

import numpy
import pytest

from openfisca_core import entities, periods, taxbenefitsystems, variables
from openfisca_core.links import Many2OneLink, One2ManyLink
from openfisca_core.simulations import SimulationBuilder


# -- Test CoreEntity.add_link / get_link / links --------------------------


class TestEntityLinks:
    """Verify that links can be registered and retrieved on entities."""

    def test_add_and_get_link(self):
        entity = entities.SingleEntity("person", "persons", "A person", "")
        link = Many2OneLink(
            name="mother",
            link_field="mother_id",
            target_entity_key="person",
        )
        entity.add_link(link)
        assert entity.get_link("mother") is link

    def test_get_link_not_found(self):
        entity = entities.SingleEntity("person", "persons", "A person", "")
        assert entity.get_link("nonexistent") is None

    def test_links_property(self):
        entity = entities.SingleEntity("person", "persons", "A person", "")
        link1 = Many2OneLink(
            name="mother",
            link_field="mother_id",
            target_entity_key="person",
        )
        link2 = Many2OneLink(
            name="father",
            link_field="father_id",
            target_entity_key="person",
        )
        entity.add_link(link1)
        entity.add_link(link2)
        assert len(entity.links) == 2
        assert "mother" in entity.links
        assert "father" in entity.links

    def test_links_empty_by_default(self):
        entity = entities.SingleEntity("person", "persons", "A person", "")
        assert entity.links == {}


# -- Test link resolution in Simulation -----------------------------------


class TestLinkResolution:
    """Verify that links are resolved when a Simulation is created."""

    def _make_tbs_with_link(self):
        """Build a minimal TBS with a person entity and a mother link."""
        person = entities.SingleEntity(
            "person", "persons", "A person", "",
        )
        household = entities.GroupEntity(
            "household",
            "households",
            "A household",
            "",
            roles=[{"key": "member"}],
        )

        # Declare a Many2One link: person → person (intra-entity)
        mother_link = Many2OneLink(
            name="mother",
            link_field="mother_id",
            target_entity_key="person",
        )
        person.add_link(mother_link)

        tbs = taxbenefitsystems.TaxBenefitSystem([person, household])

        # Add required variables
        class mother_id(variables.Variable):
            value_type = int
            default_value = -1
            entity = person
            definition_period = periods.DateUnit.ETERNITY
            label = "ID of the mother"

        tbs.add_variable(mother_id)

        return tbs, mother_link

    def test_links_resolved_after_simulation_build(self):
        tbs, mother_link = self._make_tbs_with_link()
        sim = SimulationBuilder().build_default_simulation(tbs, count=5)

        # The link should be attached to the person population
        assert mother_link._source_population is not None
        assert mother_link._target_population is not None
        assert mother_link.is_resolved

    def test_resolved_link_points_to_correct_population(self):
        tbs, mother_link = self._make_tbs_with_link()
        sim = SimulationBuilder().build_default_simulation(tbs, count=5)

        # Source and target should both be the person population
        assert mother_link._source_population is sim.persons
        assert mother_link._target_population is sim.persons

    def test_link_on_group_entity(self):
        """A link declared on a GroupEntity gets resolved too."""
        person = entities.SingleEntity(
            "person", "persons", "A person", "",
        )
        household = entities.GroupEntity(
            "household",
            "households",
            "A household",
            "",
            roles=[{"key": "member"}],
        )

        # O2M link: household → persons
        members_link = One2ManyLink(
            name="members",
            link_field="household_id",
            target_entity_key="person",
        )
        household.add_link(members_link)

        tbs = taxbenefitsystems.TaxBenefitSystem([person, household])
        sim = SimulationBuilder().build_default_simulation(tbs, count=3)

        assert members_link.is_resolved
        assert members_link._source_population is sim.populations["household"]
        assert members_link._target_population is sim.persons


# -- Test backward compatibility ------------------------------------------


class TestBackwardCompatibility:
    """Ensure that adding links doesn't break existing functionality."""

    def test_existing_tests_pass_with_country_template(self):
        """Smoke test: build a simulation with country-template."""
        try:
            from openfisca_country_template import CountryTaxBenefitSystem

            tbs = CountryTaxBenefitSystem()
            sim = SimulationBuilder().build_default_simulation(tbs, count=3)

            # Basic calculation should work
            result = sim.calculate("disposable_income", "2024-01")
            assert result is not None
            assert len(result) == 3
        except ImportError:
            pytest.skip("openfisca-country-template not installed")

    def test_no_links_no_problem(self):
        """Entities without links should work as before."""
        person = entities.SingleEntity(
            "person", "persons", "A person", "",
        )
        household = entities.GroupEntity(
            "household",
            "households",
            "A household",
            "",
            roles=[{"key": "member"}],
        )
        tbs = taxbenefitsystems.TaxBenefitSystem([person, household])
        sim = SimulationBuilder().build_default_simulation(tbs, count=2)

        # Entity should have an empty links dict
        assert person.links == {}
        assert household.links == {}

        # Simulation should work fine
        assert sim.persons.count == 2
