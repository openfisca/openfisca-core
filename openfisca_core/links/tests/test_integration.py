"""Tests for Phase 2: entity integration and link resolution."""

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
            "person",
            "persons",
            "A person",
            "",
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
        bound_link = sim.persons.links["mother"]
        assert bound_link._source_population is not None
        assert bound_link._target_population is not None
        assert bound_link.is_resolved

    def test_resolved_link_points_to_correct_population(self):
        tbs, mother_link = self._make_tbs_with_link()
        sim = SimulationBuilder().build_default_simulation(tbs, count=5)

        # Source and target should both be the person population
        bound_link = sim.persons.links["mother"]
        assert bound_link._source_population is sim.persons
        assert bound_link._target_population is sim.persons

    def test_link_on_group_entity(self):
        """A link declared on a GroupEntity gets resolved too."""
        person = entities.SingleEntity(
            "person",
            "persons",
            "A person",
            "",
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

        bound_link = sim.populations["household"].links["members"]
        assert bound_link.is_resolved
        assert bound_link._source_population is sim.populations["household"]
        assert bound_link._target_population is sim.persons


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
            "person",
            "persons",
            "A person",
            "",
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


# -- Regression test: non-default person entity key -----------------------


class TestNonDefaultPersonKey:
    """Verify that _resolve_links works when person entity key != 'person'.

    This is a regression test for the France API crash where the person
    entity is named 'individu' instead of 'person'.
    """

    def test_resolve_links_with_individu_key(self):
        """Simulation.__init__ must not crash with entity key 'individu'."""
        individu = entities.SingleEntity("individu", "individus", "Un individu", "")
        menage = entities.GroupEntity(
            "menage",
            "menages",
            "Un ménage",
            "",
            roles=[{"key": "personne_de_reference"}],
        )
        tbs = taxbenefitsystems.TaxBenefitSystem([individu, menage])
        # This line triggered the KeyError before the fix
        sim = SimulationBuilder().build_default_simulation(tbs, count=3)

        assert sim.persons.count == 3
        # Implicit links should be auto-generated with correct keys
        assert "menage" in sim.persons.links  # individu → menage (M2O)
        assert (
            "individus" in sim.populations["menage"].links
        )  # menage → individus (O2M)

    def test_implicit_link_target_uses_actual_person_key(self):
        """The O2M link target must be 'individu', not 'person'."""
        individu = entities.SingleEntity("individu", "individus", "Un individu", "")
        foyer_fiscal = entities.GroupEntity(
            "foyer_fiscal",
            "foyers_fiscaux",
            "Un foyer fiscal",
            "",
            roles=[{"key": "declarant"}],
        )
        tbs = taxbenefitsystems.TaxBenefitSystem([individu, foyer_fiscal])
        sim = SimulationBuilder().build_default_simulation(tbs, count=2)

        o2m_link = sim.populations["foyer_fiscal"].links["individus"]
        assert o2m_link.target_entity_key == "individu"
        assert o2m_link.is_resolved
        assert o2m_link._target_population is sim.persons


def test_chained_link_three_levels():
    """person -> mother -> mother -> household should compose correctly."""
    person = entities.SingleEntity("person", "persons", "A person", "")
    household = entities.GroupEntity(
        "household", "households", "A household", "", roles=[{"key": "member"}]
    )

    person.add_link(Many2OneLink("mother", "mother_id", "person"))
    person.add_link(Many2OneLink("household", "household_id", "household"))

    tbs = taxbenefitsystems.TaxBenefitSystem([person, household])

    class mother_id(variables.Variable):
        value_type = int
        entity = person
        definition_period = periods.DateUnit.ETERNITY
        default_value = -1

    class household_id(variables.Variable):
        value_type = int
        entity = person
        definition_period = periods.DateUnit.ETERNITY
        default_value = -1

    class rent(variables.Variable):
        value_type = float
        entity = household
        definition_period = periods.DateUnit.YEAR

    tbs.add_variable(mother_id)
    tbs.add_variable(household_id)
    tbs.add_variable(rent)

    sim = SimulationBuilder().build_default_simulation(
        tbs,
        count=3,
        group_members={"household": [0, 0, 0]},
    )
    sim.set_input("mother_id", "2024", [1, 2, -1])
    sim.set_input("household_id", "2024", [-1, -1, 0])
    sim.set_input("rent", "2024", [700.0])

    result = sim.persons.links["mother"].mother.household.get("rent", "2024")
    assert result[0] == pytest.approx(700.0)
