import inspect

import pytest
from numpy.testing import assert_equal

from .._builder import ContractBuilder
from .._func_checker import FuncChecker

from . import fixtures


@pytest.fixture
def this_builder():
    return ContractBuilder(["file.py"])


@pytest.fixture
def that_builder():
    return ContractBuilder(["file.py"])


def test(this_builder, that_builder):

    this_builder(inspect.getsource(fixtures.func))
    that_builder(inspect.getsource(fixtures.func))

    this, = this_builder.contracts
    that, = that_builder.contracts

    checker = FuncChecker(this, that)

    assert_equal(checker.diff_hash(), [0, 0, 0, 0])
    assert_equal(checker.diff_args(), [0, 0, 0, 0])
    assert_equal(checker.diff_name(), [0, 0, 0, 0])
    assert_equal(checker.diff_type(), [0, 0, 0, 0])
    assert_equal(checker.diff_defs(), [0, 0, 0, 0])
    assert checker.score() == 0
    assert checker.reason is None


def test_when_added_args(this_builder, that_builder):

    this_builder(inspect.getsource(fixtures.func_with_more_args))
    that_builder(inspect.getsource(fixtures.func))

    this, = this_builder.contracts
    that, = that_builder.contracts

    checker = FuncChecker(this, that)

    assert_equal(checker.diff_hash(), [1, 1, 1, 1, 1, 1])
    assert_equal(checker.diff_args(), [2, 2, 2, 2, 2, 2])
    assert_equal(checker.diff_name(), [0, 0, 0, 0, 2, 2])
    assert_equal(checker.diff_type(), [0, 0, 0, 0, 0, 0])
    assert_equal(checker.diff_defs(), [0, 0, 0, 0, 3, 3])
    assert checker.score() == 3
    assert checker.reason == "added-args"


def test_when_removed_args(this_builder, that_builder):

    this_builder(inspect.getsource(fixtures.func))
    that_builder(inspect.getsource(fixtures.func_with_more_args))

    this, = this_builder.contracts
    that, = that_builder.contracts

    checker = FuncChecker(this, that)

    assert_equal(checker.diff_hash(), [1, 1, 1, 1, 1, 1])
    assert_equal(checker.diff_args(), [3, 3, 3, 3, 3, 3])
    assert_equal(checker.diff_name(), [0, 0, 0, 0, 2, 2])
    assert_equal(checker.diff_type(), [0, 0, 0, 0, 0, 0])
    assert_equal(checker.diff_defs(), [0, 0, 0, 0, 2, 2])
    assert checker.score() == 3
    assert checker.reason == "removed-args"


def test_when_changed_arg_names(this_builder, that_builder):

    this_builder(inspect.getsource(fixtures.func_with_changed_args))
    that_builder(inspect.getsource(fixtures.func))

    this, = this_builder.contracts
    that, = that_builder.contracts

    checker = FuncChecker(this, that)

    assert_equal(checker.diff_hash(), [1, 1, 1, 1])
    assert_equal(checker.diff_args(), [0, 0, 0, 0])
    assert_equal(checker.diff_name(), [0, 3, 3, 0])
    assert_equal(checker.diff_type(), [0, 0, 0, 0])
    assert_equal(checker.diff_defs(), [0, 0, 0, 0])
    assert checker.score() == 3
    assert checker.reason == "changed-args"


def test_when_added_types(this_builder, that_builder):

    this_builder(inspect.getsource(fixtures.func_with_types))
    that_builder(inspect.getsource(fixtures.func))

    this, = this_builder.contracts
    that, = that_builder.contracts

    checker = FuncChecker(this, that)

    assert_equal(checker.diff_hash(), [1, 1, 1, 1])
    assert_equal(checker.diff_args(), [0, 0, 0, 0])
    assert_equal(checker.diff_name(), [0, 0, 0, 0])
    assert_equal(checker.diff_type(), [1, 1, 0, 0])
    assert_equal(checker.diff_defs(), [0, 0, 0, 0])
    assert checker.score() == 1
    assert checker.reason == "changed-types"


def test_when_removed_types(this_builder, that_builder):

    this_builder(inspect.getsource(fixtures.func))
    that_builder(inspect.getsource(fixtures.func_with_types))

    this, = this_builder.contracts
    that, = that_builder.contracts

    checker = FuncChecker(this, that)

    assert_equal(checker.diff_hash(), [1, 1, 1, 1])
    assert_equal(checker.diff_args(), [0, 0, 0, 0])
    assert_equal(checker.diff_name(), [0, 0, 0, 0])
    assert_equal(checker.diff_type(), [1, 1, 0, 0])
    assert_equal(checker.diff_defs(), [0, 0, 0, 0])
    assert checker.score() == 1
    assert checker.reason == "changed-types"


def test_when_added_defaults(this_builder, that_builder):

    this_builder(inspect.getsource(fixtures.func_with_defaults))
    that_builder(inspect.getsource(fixtures.func))

    this, = this_builder.contracts
    that, = that_builder.contracts

    checker = FuncChecker(this, that)

    assert_equal(checker.diff_hash(), [1, 1, 1, 1])
    assert_equal(checker.diff_args(), [0, 0, 0, 0])
    assert_equal(checker.diff_name(), [0, 0, 0, 0])
    assert_equal(checker.diff_type(), [0, 0, 0, 0])
    assert_equal(checker.diff_defs(), [0, 0, 2, 2])
    assert checker.score() == 2
    assert checker.reason == "added-defaults"


def test_when_removed_defaults(this_builder, that_builder):

    this_builder(inspect.getsource(fixtures.func))
    that_builder(inspect.getsource(fixtures.func_with_defaults))

    this, = this_builder.contracts
    that, = that_builder.contracts

    checker = FuncChecker(this, that)

    assert_equal(checker.diff_hash(), [1, 1, 1, 1])
    assert_equal(checker.diff_args(), [0, 0, 0, 0])
    assert_equal(checker.diff_name(), [0, 0, 0, 0])
    assert_equal(checker.diff_type(), [0, 0, 0, 0])
    assert_equal(checker.diff_defs(), [0, 0, 3, 3])
    assert checker.score() == 3
    assert checker.reason == "removed-defaults"


def test_when_added_args_and_defs(this_builder, that_builder):

    this_builder(inspect.getsource(fixtures.func_with_more_defaults))
    that_builder(inspect.getsource(fixtures.func))

    this, = this_builder.contracts
    that, = that_builder.contracts

    checker = FuncChecker(this, that)

    assert_equal(checker.diff_hash(), [1, 1, 1, 1, 1, 1])
    assert_equal(checker.diff_args(), [2, 2, 2, 2, 2, 2])
    assert_equal(checker.diff_name(), [0, 0, 0, 0, 2, 2])
    assert_equal(checker.diff_type(), [0, 0, 0, 0, 0, 0])
    assert_equal(checker.diff_defs(), [0, 0, 0, 0, 0, 0])
    assert checker.score() == 2
    assert checker.reason == "added-args-with-defaults"
