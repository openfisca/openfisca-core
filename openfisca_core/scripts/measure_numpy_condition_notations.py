#! /usr/bin/env python
# -*- coding: utf-8 -*-


"""
Measure and compare different vectorial condition notations:
- using multiplication notation: (choice == 1) * choice_1_value + (choice == 2) * choice_2_value
- using np.select: the same than multiplication but more idiomatic like a "switch" control-flow statement
- using np.fromiter: iterates in Python over the array and calculates lazily only the required values

The aim of this script is to compare the time taken by the calculation of the values
"""
from __future__ import unicode_literals, print_function, division, absolute_import
from contextlib import contextmanager
import argparse
import sys
import time

import numpy as np

from openfisca_core.commons import to_unicode


args = None


@contextmanager
def measure_time(title):
    t1 = time.time()
    yield
    t2 = time.time()
    print('{}\t: {:.8f} seconds elapsed'.format(title, t2 - t1).encode('utf-8'))


def switch_fromiter(conditions, function_by_condition, dtype):
    value_by_condition = {}

    def get_or_store_value(condition):
        if condition not in value_by_condition:
            value = function_by_condition[condition]()
            value_by_condition[condition] = value
        return value_by_condition[condition]

    return np.fromiter(
        (
            get_or_store_value(condition)
            for condition in conditions
            ),
        dtype,
        )


def switch_select(conditions, value_by_condition):
    condlist = [
        conditions == condition
        for condition in value_by_condition.keys()
        ]
    return np.select(condlist, value_by_condition.values())


def calculate_choice_1_value():
    time.sleep(args.calculate_time)
    return 80


def calculate_choice_2_value():
    time.sleep(args.calculate_time)
    return 90


def calculate_choice_3_value():
    time.sleep(args.calculate_time)
    return 95


def test_multiplication(choice):
    choice_1_value = calculate_choice_1_value()
    choice_2_value = calculate_choice_2_value()
    choice_3_value = calculate_choice_3_value()
    result = (choice == 1) * choice_1_value + (choice == 2) * choice_2_value + (choice == 3) * choice_3_value
    return result


def test_switch_fromiter(choice):
    result = switch_fromiter(
        choice,
        {
            1: calculate_choice_1_value,
            2: calculate_choice_2_value,
            3: calculate_choice_3_value,
            },
        dtype = np.int,
        )
    return result


def test_switch_select(choice):
    choice_1_value = calculate_choice_1_value()
    choice_2_value = calculate_choice_2_value()
    choice_3_value = calculate_choice_2_value()
    result = switch_select(
        choice,
        {
            1: choice_1_value,
            2: choice_2_value,
            3: choice_3_value,
            },
        )
    return result


def test_all_notations():
    # choice is an array with 1 and 2 items like [2, 1, ..., 1, 2]
    choice = np.random.randint(2, size = args.array_length) + 1

    with measure_time('multiplication'):
        test_multiplication(choice)

    with measure_time('switch_select'):
        test_switch_select(choice)

    with measure_time('switch_fromiter'):
        test_switch_fromiter(choice)


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--array-length', default = 1000, type = int, help = "length of the array")
    parser.add_argument('--calculate-time', default = 0.1, type = float,
        help = "time taken by the calculation in seconds")
    global args
    args = parser.parse_args()

    print(to_unicode(args).encode('utf-8'))
    test_all_notations()


if __name__ == "__main__":
    sys.exit(main())
