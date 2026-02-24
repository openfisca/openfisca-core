import numpy


def test_syntax(sim):
    # person.household string attribute access
    rents = sim.persons.household("rent", "2024")
    assert numpy.array_equal(rents, [800.0, 800.0, 500.0, 100.0])

    # household.persons aggregation
    salaries = sim.populations["household"].persons.sum("salary", "2024")
    assert numpy.array_equal(salaries, [1500.0, 2000.0, 100.0])
