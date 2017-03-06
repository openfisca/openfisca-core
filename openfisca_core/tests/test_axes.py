from openfisca_core.tools import assert_near
from dummy_country import DummyTaxBenefitSystem


tax_benefit_system = DummyTaxBenefitSystem()


# Test introduced following a bug with set_input in the case of parallel axes
def test_set_input_parallel_axes():
    year = 2013
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            [
                dict(
                    count = 3,
                    index = 0,
                    name = 'salaire_brut',
                    max = 100000,
                    min = 0,
                    ),
                dict(
                    count = 3,
                    index = 1,
                    name = 'salaire_brut',
                    max = 100000,
                    min = 0,
                    ),
                ],
            ],
        period = year,
        parent1 = {},
        parent2 = {},
        enfants = [{"salaire_brut": 2000}]
        ).new_simulation()

    assert_near(
        simulation.calculate_add('salaire_brut', year),
        [0, 0, 2000, 50000, 50000, 2000, 100000, 100000, 2000],
        absolute_error_margin = 0.01
        )
