# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
from builtins import str
import collections
import datetime
import re

import numpy as np

from openfisca_core import conv, periods
from openfisca_core.indexed_enums import Enum
from openfisca_core.commons import basestring_type, to_unicode

"""
Columns are the ancestors of Variables, and are now considered deprecated. Preferably use `Variable` instead.
Columns have not been removed from the code, as they are still used by the legacy API and by some reusers (especially for simulations with a big population)
If you do need a column for retro-compatibility, you can use: column = make_column_from_variable(variable)
"""


def N_(message):
    return message


year_or_month_or_day_re = re.compile(r'(18|19|20)\d{2}(-(0?[1-9]|1[0-2])(-([0-2]?\d|3[0-1]))?)?$')


# Base Column

def make_column_from_variable(variable):
    CONVERSION_MAP = {
        bool: BoolCol,
        int: IntCol,
        float: FloatCol,
        str: StrCol,
        bytes: StrCol,
        Enum: EnumCol,
        datetime.date: DateCol,
        }
    if variable.value_type == str and variable.max_length:
        return FixedStrCol(variable)
    return CONVERSION_MAP[variable.value_type](variable)


class Column(object):
    val_type = None

    def __init__(self, variable):
        self.variable = variable

    def __getattr__(self, name):
        return getattr(self.variable, name)

    def empty_clone(self):
        return self.__class__()

    def json_default(self):
        return self.default_value

    def make_json_to_array_by_period(self, period):
        return conv.condition(
            conv.test_isinstance(dict),
            conv.pipe(
                # Value is a dict of (period, value) couples.
                conv.uniform_mapping(
                    conv.pipe(
                        conv.function(periods.period),
                        conv.not_none,
                        ),
                    conv.pipe(
                        conv.make_item_to_singleton(),
                        conv.uniform_sequence(
                            self.json_to_dated_python,
                            ),
                        conv.empty_to_none,
                        conv.function(lambda cells_list: np.array(cells_list, dtype = self.dtype)),
                        ),
                    drop_none_values = True,
                    ),
                conv.empty_to_none,
                ),
            conv.pipe(
                conv.make_item_to_singleton(),
                conv.uniform_sequence(
                    self.json_to_dated_python,
                    ),
                conv.empty_to_none,
                conv.function(lambda cells_list: np.array(cells_list, dtype = self.dtype)),
                conv.function(lambda array: {period: array}),
                ),
            )

    @property
    def json_to_python(self):
        return conv.condition(
            conv.test_isinstance(dict),
            conv.pipe(
                # Value is a dict of (period, value) couples.
                conv.uniform_mapping(
                    conv.pipe(
                        conv.function(periods.period),
                        conv.not_none,
                        ),
                    self.json_to_dated_python,
                    ),
                ),
            self.json_to_dated_python,
            )

    def to_json(self):
        self_json = collections.OrderedDict((
            ('@type', self.json_type),
            ))
        if self.cerfa_field is not None:
            self_json['cerfa_field'] = self.cerfa_field
        if self.default_value is not None:
            self_json['default'] = self.json_default()
        end = self.end
        if end is not None:
            if isinstance(end, datetime.date):
                end = end.isoformat()
            self_json['end'] = end
        if self.entity is not None:
            self_json['entity'] = self.entity.key
        if self.label is not None:
            self_json['label'] = self.label
        if self.name is not None:
            self_json['name'] = self.name
        if self.reference is not None:
            self_json['reference'] = self.reference
        if self.val_type is not None:
            self_json['val_type'] = self.val_type
        return self_json

    def transform_dated_value_to_json(self, value, use_label = False):
        # Convert a non-NumPy Python value to JSON.
        return value

    def transform_value_to_json(self, value, use_label = False):
        # Convert a non-NumPy Python value to JSON.
        if isinstance(value, dict):
            return collections.OrderedDict(
                (str(period), self.transform_dated_value_to_json(dated_value, use_label = use_label))
                for period, dated_value in value.items()
                )
        return self.transform_dated_value_to_json(value, use_label = use_label)


# Level-1 Columns


class BoolCol(Column):
    '''
    A column of boolean
    '''

    @property
    def input_to_dated_python(self):
        return conv.guess_bool

    @property
    def json_to_dated_python(self):
        return conv.pipe(
            conv.test_isinstance((basestring_type, bool, int)),
            conv.guess_bool,
            )


class DateCol(Column):
    '''
    A column of Datetime 64 to store dates of people
    '''
    val_type = 'date'

    @property
    def input_to_dated_python(self):
        return conv.pipe(
            conv.test(year_or_month_or_day_re.match, error = N_('Invalid date')),
            conv.function(lambda birth: '-'.join((birth.split('-') + ['01', '01'])[:3])),
            conv.iso8601_input_to_date,
            )

    def json_default(self):
        default = np.array(self.default_value, self.dtype)
        return to_unicode(default)

    @property
    def json_to_dated_python(self):
        return conv.pipe(
            conv.condition(
                conv.test_isinstance(datetime.date),
                conv.noop,
                conv.condition(
                    conv.test_isinstance(int),
                    conv.pipe(
                        conv.test_between(1870, 2099),
                        conv.function(lambda year: datetime.date(year, 1, 1)),
                        ),
                    conv.pipe(
                        conv.test_isinstance(basestring_type),
                        conv.test(year_or_month_or_day_re.match, error = N_('Invalid date')),
                        conv.function(lambda birth: '-'.join((birth.split('-') + ['01', '01'])[:3])),
                        conv.iso8601_input_to_date,
                        ),
                    ),
                ),
            conv.test_between(datetime.date(1870, 1, 1), datetime.date(2099, 12, 31)),
            )

    def transform_dated_value_to_json(self, value, use_label = False):
        # Convert a non-NumPy Python value to JSON.
        return value.isoformat() if value is not None else value


class FixedStrCol(Column):

    @property
    def input_to_dated_python(self):
        return conv.test(lambda value: len(value) <= self.variable.max_length)

    @property
    def json_to_dated_python(self):
        return conv.pipe(
            conv.condition(
                conv.test_isinstance((float, int)),
                # YAML stores strings containing only digits as numbers.
                conv.function(str),
                ),
            conv.test_isinstance(basestring_type),
            conv.test(lambda value: len(value) <= self.variable.max_length),
            )


class FloatCol(Column):
    '''
    A column of float 32
    '''
    @property
    def input_to_dated_python(self):
        return conv.input_to_float

    @property
    def json_to_dated_python(self):
        return conv.pipe(
            conv.test_isinstance((float, int, basestring_type)),
            conv.make_anything_to_float(accept_expression = True),
            )


class IntCol(Column):
    '''
    A column of integer
    '''
    @property
    def input_to_dated_python(self):
        return conv.input_to_int

    @property
    def json_to_dated_python(self):
        return conv.pipe(
            conv.test_isinstance((int, basestring_type)),
            conv.make_anything_to_int(accept_expression = True),
            )


class StrCol(Column):

    @property
    def input_to_dated_python(self):
        return conv.noop

    @property
    def json_to_dated_python(self):
        return conv.pipe(
            conv.condition(
                conv.test_isinstance((float, int)),
                # YAML stores strings containing only digits as numbers.
                conv.function(str),
                ),
            conv.test_isinstance(basestring_type),
            )


# Level-2 Columns


class AgeCol(IntCol):
    '''
    A column of Int to store ages of people
    '''

    @property
    def input_to_dated_python(self):
        return conv.pipe(
            super(AgeCol, self).input_to_dated_python,
            conv.first_match(
                conv.test_greater_or_equal(0),
                conv.test_equals(-9999),
                ),
            )

    @property
    def json_to_dated_python(self):
        return conv.pipe(
            super(AgeCol, self).json_to_dated_python,
            conv.first_match(
                conv.test_greater_or_equal(0),
                conv.test_equals(-9999),
                ),
            )


class EnumCol(Column):
    '''
    Column of Enum objects
    '''
    dtype = np.dtype('object')
    is_period_size_independent = True
    json_type = 'Enumeration'
    index_by_slug = None

    @property
    def input_to_dated_python(self):
        enum = self.variable.possible_values
        if enum is None:
            return conv.test_isinstance(basestring_type)
        return conv.pipe(
            # Verify that item index belongs to enumeration.
            conv.test_in([item.name for item in list(enum)])
            )

    def json_default(self):
        default = self.default_value
        if default is not None:
            to_unicode(default)
        return default

    @property
    def json_to_dated_python(self):
        enum = self.variable.possible_values
        possible_names = [item.name for item in list(enum)]

        if enum is None:
            return conv.pipe(
                conv.test_isinstance(basestring_type)
                )
        return conv.pipe(
            conv.test_isinstance(basestring_type),
            conv.pipe(
                # Verify that item belongs to enumeration.
                conv.test_in(possible_names),
                # Transform that item into enum object.
                conv.function(lambda enum_name: enum[enum_name])
                )
            )

    def to_json(self):
        self_json = super(EnumCol, self).to_json()
        if self.variable.possible_values is not None:
            self_json['labels'] = collections.OrderedDict(
                (item.name, item.value)
                for item in self.variable.possible_values
                )
        return self_json

    def transform_dated_value_to_json(self, value, use_label = False):
        # Convert a non-NumPy Python value to JSON.
        if isinstance(value, int):
            value = [item for item in self.variable.possible_values if item.index == value][0]
        if use_label and self.variable.possible_values is not None:
            return value.value
        return value.name
