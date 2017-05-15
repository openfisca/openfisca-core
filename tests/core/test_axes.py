from openfisca_core.tools import assert_near
from openfisca_core import conv
from openfisca_core.scenarios import AbstractScenario
from openfisca_country_template import CountryTaxBenefitSystem


# To initialize a simulation with axes, we need a specific scenario.
class AxesScenario(AbstractScenario):
    def init_single_entity(self, axes = None, enfants = None, famille = None, parent1 = None, parent2 = None,
            period = None):
        if enfants is None:
            enfants = []
        assert parent1 is not None
        famille = famille.copy() if famille is not None else {}
        individus = []
        for index, individu in enumerate([parent1, parent2] + (enfants or [])):
            if individu is None:
                continue
            id = individu.get('id')
            if id is None:
                individu = individu.copy()
                individu['id'] = id = 'ind{}'.format(index)
            individus.append(individu)
            if index <= 1:
                famille.setdefault('parents', []).append(id)
            else:
                famille.setdefault('children', []).append(id)
        conv.check(self.make_json_or_python_to_attributes())(dict(
            axes = axes,
            period = period,
            test_case = dict(
                households = [famille],
                persons = individus,
                ),
            ))
        return self


tax_benefit_system = CountryTaxBenefitSystem()
tax_benefit_system.Scenario = AxesScenario


# Test introduced following a bug with set_input in the case of parallel axes
def test_set_input_parallel_axes():
    year = "2016-01"
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            [
                dict(
                    count = 3,
                    index = 0,
                    name = 'salary',
                    max = 100000,
                    min = 0,
                    ),
                dict(
                    count = 3,
                    index = 1,
                    name = 'salary',
                    max = 100000,
                    min = 0,
                    ),
                ],
            ],
        period = year,
        parent1 = {},
        parent2 = {},
        enfants = [{"salary": 2000}]
        ).new_simulation()

    assert_near(
        simulation.calculate_add('salary', year),
        [0, 0, 2000, 50000, 50000, 2000, 100000, 100000, 2000],
        absolute_error_margin = 0.01
        )


def test_1_axis():
    period = "2016-01"
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            dict(
                count = 3,
                name = 'salary',
                max = 3000,
                min = 0,
                ),
            ],
        period = period,
        parent1 = {},
        ).new_simulation()
    assert_near(
        simulation.calculate('salary', period),
        [0, 1500, 3000]
        )


def test_2_parallel_axes():
    period = "2016-01"
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            [
                dict(
                    count = 3,
                    name = 'salary',
                    max = 10000,
                    min = 0,
                    ),
                dict(
                    count = 3,
                    index = 1,
                    name = 'salary',
                    max = 1000,
                    min = 0,
                    ),
                ],
            ],
        period = period,
        parent1 = {},
        parent2 = {},
        ).new_simulation()
    assert_near(
        simulation.calculate('salary', period),
        [0, 0, 5000, 500, 10000, 1000]
        )


def test_2_parallel_axes_different_periods():
    period_1 = "2016-01"
    period_2 = "2016-02"

    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            [
                dict(
                    count = 3,
                    name = 'salary',
                    max = 1200,
                    min = 0,
                    period = period_1,
                    ),
                dict(
                    count = 3,
                    index = 1,
                    name = 'salary',
                    max = 1200,
                    min = 0,
                    period = period_2,
                    ),
                ],
            ],
        period = period_2,
        parent1 = {},
        parent2 = {},
        ).new_simulation()

    assert_near(simulation.calculate('salary', period_1), [0, 0, 600, 0, 1200, 0])
    assert_near(simulation.calculate_add('salary', period_2), [0, 0, 0, 600, 0, 1200])


def check_disposable_income(period, expected_disposable_income):
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        axes = [
            dict(
                count = 5,
                name = 'salary',
                max = 10000,
                min = 0,
                ),
            ],
        period = period,
        parent1 = dict(),
        ).new_simulation()
    disposable_income = simulation.calculate('disposable_income', period)
    assert_near(disposable_income, expected_disposable_income, absolute_error_margin = 0.005)


def test_disposable_income():
    yield check_disposable_income, "2015-01", [0, 2025, 4050, 6075, 8100]
    yield check_disposable_income, "2016-01", [600, 2025, 4050, 6075, 8100]
    yield check_disposable_income, "2017-01", [600, 2675, 4750, 6765, 8740]
