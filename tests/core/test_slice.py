from openfisca_core.data_storage import InMemoryStorage
# from openfisca_core.entities import Entity
# from openfisca_core.holders import Holder
# from openfisca_core.periods import DateUnit
# from openfisca_core.populations import Population
# from openfisca_core.variables import Variable
from openfisca_core.simulations import SimulationBuilder
from openfisca_core.tools import assert_near


def test_in_memory_storage():
    storage = InMemoryStorage(is_eternal=True)
    storage.put([1,2,3], period=None)

    sliced_clone = storage.slice([1, 2])

    value = sliced_clone.get()
    assert value == [2, 3]


# def test_holder():
#     base_entity = Entity("key", "plural", "label", "doc")

#     class base_variable(Variable):
#         value_type = int
#         entity = base_entity
#         definition_period = DateUnit.MONTH

#     population = Population(base_entity)
#     holder = Holder(base_variable, population)
#     value = [1,2,3]
#     period = "period"
#     holder.put_in_cache(value, period)

# def test_ordered_slice(tax_benefit_system) -> None:
#     period = "2017-01"
#     simulation = SimulationBuilder().build_from_entities(
#         tax_benefit_system,
#         {
#             "persons": {
#                 "bill": {"salary": {period: 3000}},
#                 "alice": {"salary": {period: 6000}},
#             },
#             "households": {
#                 "bob_household": {"adults": ["bill"], "accommodation_size": {period: 2}},
#                 "alice_household": {"adults": ["alice"], "accommodation_size": {period: 1}},
#             },
#         },
#     )

#     simulation_clone = simulation.slice([1]) # Alice
#     salaries = simulation_clone.calculate("salary", period)
#     sizes = simulation_clone.calculate("accommodation_size", period)
#     assert simulation != simulation_clone
#     assert len(simulation_clone.persons.ids) == 1
#     assert_near(salaries, [6000])
#     assert_near(sizes, [1])


def test_unordered_slice(tax_benefit_system) -> None:
    period = "2017-01"
    simulation = SimulationBuilder().build_from_entities(
        tax_benefit_system,
        {
            "persons": {
                "alice": {"salary": {period: 6000}},
                "bill": {"salary": {period: 3000}},
            },
            "households": {
                "bob_household": {"adults": ["bill"], "accommodation_size": {period: 2}},
                "alice_household": {"adults": ["alice"], "accommodation_size": {period: 1}},
            },
        },
    )

    simulation_clone = simulation.slice([0]) # Alice
    salaries = simulation_clone.calculate("salary", period)
    sizes = simulation_clone.calculate("accommodation_size", period)
    assert simulation != simulation_clone
    assert len(simulation_clone.persons.ids) == 1
    assert_near(salaries, [6000])
    assert_near(sizes, [1])

