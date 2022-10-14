def test_parameter_homogenization():
    from policyengine_core.parameters import ParameterNode
    import numpy as np

    # Create the parameter

    root = ParameterNode(
        data={
            "value_by_country_and_region": {
                "ENGLAND": {
                    "NORTH_EAST": {
                        1: {
                            "2021-01-01": 1,
                        }
                    }
                },
                "metadata": {
                    "breakdown": ["country", "region", "range(1, 4)"],
                },
            }
        }
    )

    from policyengine_core.model_api import Enum, Variable, ETERNITY
    from policyengine_core.entities import Entity

    Person = Entity("person", "people", "Person", "A person")

    class Country(Enum):
        ENGLAND = "England"
        SCOTLAND = "Scotland"
        WALES = "Wales"
        NORTHERN_IRELAND = "Northern Ireland"

    class country(Variable):
        value_type = Enum
        entity = Person
        definition_period = ETERNITY
        possible_values = Country
        default_value = Country.ENGLAND

    class Region(Enum):
        NORTH_EAST = "North East"
        NORTH_WEST = "North West"
        SOUTH_EAST = "South East"
        SOUTH_WEST = "South West"
        LONDON = "London"
        EAST_OF_ENGLAND = "East of England"
        WALES = "Wales"
        SCOTLAND = "Scotland"
        WEST_MIDLANDS = "West Midlands"
        NORTHERN_IRELAND = "Northern Ireland"
        EAST_MIDLANDS = "East Midlands"
        YORKSHIRE = "Yorkshire and The Humber"

    class region(Variable):
        value_type = Enum
        entity = Person
        definition_period = ETERNITY
        possible_values = Region
        default_value = Region.NORTH_EAST

    class family_size(Variable):
        value_type = int
        entity = Person
        definition_period = ETERNITY

    from policyengine_core.parameters import homogenize_parameter_structures
    from policyengine_core.taxbenefitsystems import TaxBenefitSystem

    system = TaxBenefitSystem([Person])
    system.add_variables(country, region, family_size)
    system.parameters = root

    system.parameters = homogenize_parameter_structures(
        system.parameters, system.variables, default_value=0
    )

    countries = np.array(["ENGLAND", "ENGLAND", "SCOTLAND"])
    regions = np.array(["NORTH_EAST", "LONDON", "SCOTLAND"])
    family_sizes = np.array([1, 2, 3])

    assert (
        system.parameters("2021-01-01").value_by_country_and_region[countries][
            regions
        ][family_sizes]
        == [1, 0, 0]
    ).all()
