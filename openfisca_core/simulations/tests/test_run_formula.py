from __future__ import annotations

from numpy.typing import NDArray
from openfisca_core.simulations.typing import (
    Formula2,
    Formula3,
    Instant,
    ParameterNodeAtInstant,
    Params,
    Population,
)
from typing import Any

import numpy
import pytest

from openfisca_core import simulations


class TestPopulation:
    ...


class TestInstant:
    ...


class TestParams:
    def __call__(self, instant: Instant) -> ParameterNodeAtInstant:
        ...


@pytest.fixture
def population() -> Population:
    return TestPopulation()


@pytest.fixture
def instant() -> Instant:
    return TestInstant()


@pytest.fixture
def params() -> Params:
    return TestParams()


def test_run_formula_without_formula(
    population: Population, instant: Instant, params: Params
) -> None:
    """Test that RunFormula runs without a formula."""

    run_formula = simulations.RunFormula(None)

    assert not run_formula(population, instant, params)


def test_run_formula_with_two_arguments(
    population: Population, instant: Instant, params: Params
) -> None:
    """Test that RunFormula runs a formula with two arguments."""

    def formula(a: Population, b: Instant) -> NDArray[Any]:
        return numpy.array([1, 2, 3])

    run_formula = simulations.RunFormula(formula)

    assert run_formula(population, instant, params)


def test_run_formula_with_three_arguments(
    population: Population, instant: Instant, params: Params
) -> None:
    """Test that RunFormula runs a formula with three arguments."""

    def formula(a: Population, b: Instant, c: Params) -> NDArray[Any]:
        return numpy.array([1, 2, 3])

    run_formula = simulations.RunFormula(formula)

    assert run_formula(population, instant, params)
