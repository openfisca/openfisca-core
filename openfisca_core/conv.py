# -*- coding: utf-8 -*-


"""Conversion functions"""

from __future__ import unicode_literals, print_function, division, absolute_import

from biryani.baseconv import *  # noqa
from biryani.datetimeconv import *  # noqa
from biryani.jsonconv import *  # noqa
from biryani.states import State


default_state = State()


def add_ancestor_to_state(state, ancestor):
    if state is None:
        state = default_state
    if getattr(state, 'ancestors', None) is None:
        state.ancestors = []
    state.ancestors.append(ancestor)
    return state


def anything_to_strict_int(value, state = None):
    """Convert any python data to an integer.

    .. warning:: Like most converters, a ``None`` value is not converted.

    >>> anything_to_strict_int(42)
    (42, None)
    >>> anything_to_strict_int('42')
    (42, None)
    >>> anything_to_strict_int('42')
    (42, None)
    >>> anything_to_strict_int(42.0)
    (42, None)
    >>> anything_to_strict_int(42.75)
    (42.75, 'Value must be an integer')
    >>> anything_to_strict_int('42.75')
    ('42.75', 'Value must be an integer')
    >>> anything_to_strict_int('42,75')
    ('42,75', 'Value must be an integer')
    >>> anything_to_strict_int(None)
    (None, None)
    """
    if value is None:
        return value, None
    if state is None:
        state = default_state
    if isinstance(value, int):
        return int(value), None
    try:
        float_value = float(value)
        int_value = int(float_value)
    except ValueError:
        return value, state._('Value must be an integer')
    if float_value != int_value:
        return value, state._('Value must be an integer')
    return int_value, None


def embed_error(value, error_key, error):
    """Embed errors inside value."""
    if error is None:
        return None
    if isinstance(value, dict):
        if isinstance(error, dict):
            for child_key, child_error in error.items():
                child_error = embed_error(value.get(child_key), error_key, child_error)
                if child_error is not None:
                    value.setdefault(error_key, {})[child_key] = child_error
        else:
            value[error_key] = error
        return None
    if isinstance(value, list) and isinstance(error, dict):
        if all(isinstance(key, int) and 0 <= key < len(value) for key in error):
            for child_index, child_error in error.items():
                child_error = embed_error(value[child_index], error_key, child_error)
                if child_error is not None:
                    return error
            return None
        if all(isinstance(key, basestring) and key.isdigit() and 0 <= int(key) < len(value) for key in error):
            for child_key, child_error in error.items():
                child_error = embed_error(value[int(child_key)], error_key, child_error)
                if child_error is not None:
                    return error
            return None
    return error


input_to_strict_int = pipe(cleanup_line, anything_to_strict_int)
"""Convert a string to an integer.

    >>> input_to_strict_int('42')
    (42, None)
    >>> input_to_strict_int('   42   ')
    (42, None)
    >>> input_to_strict_int('42.0')
    (42, None)
    >>> input_to_strict_int('42.75')
    ('42.75', 'Value must be an integer')
    >>> input_to_strict_int('42,75')
    ('42,75', 'Value must be an integer')
    >>> input_to_strict_int(None)
    (None, None)
    """


json_to_natural_int = pipe(
    test_isinstance(int),
    test_greater_or_equal(0),
    )


def remove_ancestor_from_state(state, ancestor):
    assert state.ancestors.pop() is ancestor
    if len(state.ancestors) == 0:
        del state.ancestors


def test_in_pop(values, error = None):
    def remove(value):
        values.remove(value)
        return value

    return pipe(
        test_in(values, error = error),
        function(remove),
        )
