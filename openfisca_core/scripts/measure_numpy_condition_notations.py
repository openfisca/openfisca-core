#! /usr/bin/env python
# flake8: noqa T001


"""Measure and compare different vectorial condition notations:
- using multiplication notation: (choice == 1) * choice_1_value + (choice == 2) * choice_2_value
- using numpy.select: the same than multiplication but more idiomatic like a "switch" control-flow statement
- using numpy.fromiter: iterates in Python over the array and calculates lazily only the required values.

The aim of this script is to compare the time taken by the calculation of the values
"""

import argparse
import sys
import time
from contextlib import contextmanager

import numpy

args = None


@contextmanager
def measure_time(title):
    time.time()
    yield
    time.time()


def switch_fromiter(conditions, function_by_condition, dtype):
    value_by_condition = {}

    def get_or_store_value(condition):
        if condition not in value_by_condition:
            value = function_by_condition[condition]()
            value_by_condition[condition] = value
        return value_by_condition[condition]

    return numpy.fromiter(
        (get_or_store_value(condition) for condition in conditions),
        dtype,
    )


def switch_select(conditions, value_by_condition):
    condlist = [conditions == condition for condition in value_by_condition]
    return numpy.select(condlist, value_by_condition.values())


def calculate_choice_1_value() -> int:
    time.sleep(args.calculate_time)
    return 80


def calculate_choice_2_value() -> int:
    time.sleep(args.calculate_time)
    return 90


def calculate_choice_3_value() -> int:
    time.sleep(args.calculate_time)
    return 95


def test_multiplication(choice):
    choice_1_value = calculate_choice_1_value()
    choice_2_value = calculate_choice_2_value()
    choice_3_value = calculate_choice_3_value()
    return (
        (choice == 1) * choice_1_value
        + (choice == 2) * choice_2_value
        + (choice == 3) * choice_3_value
    )


def test_switch_fromiter(choice):
    return switch_fromiter(
        choice,
        {
            1: calculate_choice_1_value,
            2: calculate_choice_2_value,
            3: calculate_choice_3_value,
        },
        dtype=int,
    )


def test_switch_select(choice):
    choice_1_value = calculate_choice_1_value()
    choice_2_value = calculate_choice_2_value()
    choice_3_value = calculate_choice_2_value()
    return switch_select(
        choice,
        {
            1: choice_1_value,
            2: choice_2_value,
            3: choice_3_value,
        },
    )


def test_all_notations() -> None:
    # choice is an array with 1 and 2 items like [2, 1, ..., 1, 2]
    choice = numpy.random.randint(2, size=args.array_length) + 1

    with measure_time("multiplication"):
        test_multiplication(choice)

    with measure_time("switch_select"):
        test_switch_select(choice)

    with measure_time("switch_fromiter"):
        test_switch_fromiter(choice)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--array-length",
        default=1000,
        type=int,
        help="length of the array",
    )
    parser.add_argument(
        "--calculate-time",
        default=0.1,
        type=float,
        help="time taken by the calculation in seconds",
    )
    global args
    args = parser.parse_args()

    test_all_notations()


if __name__ == "__main__":
    sys.exit(main())
