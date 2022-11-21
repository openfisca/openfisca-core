import pytest

from openfisca_core.simulations import (
    Axes,
    Axis,
    AddParallelAxis,
    AddPerpendicularAxis,
    )


@pytest.fixture
def axes():
    return Axes()


@pytest.fixture
def axes_params(axis_params):
    return [
        [axis_params, axis_params],
        [axis_params],
        [axis_params]
    ]


@pytest.fixture
def axis_params():
    return {
        "name": "salary",
        "count": 3,
        "min": 0,
        "max": 3000,
        }


def test_add_parallel_axis(axes, axis_params):
    axis = AddParallelAxis(axes)(axis_params).parallel[-1]
    assert axis.name == "salary"
    assert axis.index == 0
    assert not axis.period


def test_add_two_parallel_axes(axes, axis_params):
    axes = AddParallelAxis(axes)(axis_params)
    axes = AddParallelAxis(axes)(axis_params).parallel
    assert [axis.name for axis in axes] == ["salary", "salary"]
    assert [axis.index for axis in axes] == [0, 1]
    assert [axis.period for axis in axes] == [None, None]


def test_add_perpendicular_axis(axes, axis_params):
    axis = AddPerpendicularAxis(axes)(axis_params).perpendicular[-1]
    assert axis.name == "salary"
    assert axis.index == 0
    assert not axis.period


def test_add_two_perpendicular_axes(axes, axis_params):
    axes = AddPerpendicularAxis(axes)(axis_params)
    axes = AddPerpendicularAxis(axes)(axis_params).perpendicular
    assert [axis.name for axis in axes] == ["salary", "salary"]
    assert [axis.index for axis in axes] == [0, 0]
    assert [axis.period for axis in axes] == [None, None]
