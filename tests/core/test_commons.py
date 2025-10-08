import numpy

from openfisca_core.commons import eval_expression


def test_sum() -> None:
    assert (eval_expression("1 + 2"), 3)


def test_string() -> None:
    assert (eval_expression("salary"), "salary")


def test_string_with_space() -> None:
    assert (eval_expression("date of birth"), "date of birth")
