def test_microsimulation():
    from policyengine_core.country_template import Microsimulation

    sim = Microsimulation()

    sim.calculate("income_tax", "2022-01")
