# -*- coding: utf-8 -*-

from pytest import fixture

from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_country_template import CountryTaxBenefitSystem


@fixture
def tax_benefit_system():
    return CountryTaxBenefitSystem()


@fixture
def period():
    return "2016-01"


@fixture
def make_simulation(tax_benefit_system, period):
    def _make_simulation(data):
        builder = SimulationBuilder()
        builder.default_period = period
        return builder.build_from_variables(tax_benefit_system, data)
    return _make_simulation


@fixture
def make_isolated_simulation(period):
    def _make_simulation(tbs, data):
        builder = SimulationBuilder()
        builder.default_period = period
        return builder.build_from_variables(tbs, data)
    return _make_simulation
