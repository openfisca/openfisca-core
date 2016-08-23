
import datetime
import re

from biryani import strings

import conv
import periods
from .enumerations import Enum
from .node import Node


def N_(message):
    return message


COLUMNS = Enum([
    'bool',
    'float',
    'date',
    'int',
    'age',
    'enum',
    ])

year_or_month_or_day_re = re.compile(ur'(18|19|20)\d{2}(-(0?[1-9]|1[0-2])(-([0-2]?\d|3[0-1]))?)?$')

class Variable(object):
    function = None

    def __init__(self, simulation):
        self.simulation = simulation
        self._array_by_period = {}     # period (+ extra params) -> value

    def set_input(self, array, period=None):
        self.put_in_cache(array, period)

    def put_in_cache(self, value, period, extra_params=None):
        if self.is_permanent:
            self.array = value
            return

        assert period is not None
        if extra_params is None:
            self._array_by_period[period] = value
        else:
            if self._array_by_period.get(period) is None:
                self._array_by_period[period] = {}
            self._array_by_period[period][tuple(extra_params)] = value

        return

    def get_from_cache(self, period, extra_params=None):
        if self.is_permanent:
            return self.array

        assert period is not None
        if self._array_by_period is not None:
            values = self._array_by_period.get(period)
            if values is not None:
                if extra_params:
                    return values.get(tuple(extra_params))
                else:
                    if(type(values) == dict):
                        return values.values()[0]
                    return values
        return None

    def get_array(self, period, extra_params=None):
        return self.get_from_cache(period, extra_params)

    def calculate(self, period, caller_name, **extra_params):
        value = self.get_from_cache(period, extra_params)

        if value:
            return Node(value, self.entity, self.simulation)

        period, node = self.base_function(self.simulation, period, **extra_params)

        return node

    @property
    def _array(self):
        return Node(self.array, self.entity, self.simulation)

    @classmethod
    def json_to_python(cls):
        return conv.condition(
            conv.test_isinstance(dict),
            conv.pipe(
                # Value is a dict of (period, value) couples.
                conv.uniform_mapping(
                    conv.pipe(
                        periods.json_or_python_to_period,
                        conv.not_none,
                        ),
                    cls.json_to_dated_python(),
                    ),
                ),
            cls.json_to_dated_python(),
            )

    @classmethod
    def json_to_dated_python(cls):
        if cls.column_type == 'BoolCol':
            return conv.pipe(
                conv.test_isinstance((basestring, bool, int)),
                conv.guess_bool,
                )
        elif cls.column_type == 'DateCol':
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
                            conv.test_isinstance(basestring),
                            conv.test(year_or_month_or_day_re.match, error=N_(u'Invalid date')),
                            conv.function(lambda birth: u'-'.join((birth.split(u'-') + [u'01', u'01'])[:3])),
                            conv.iso8601_input_to_date,
                            ),
                        ),
                    ),
                conv.test_between(datetime.date(1870, 1, 1), datetime.date(2099, 12, 31)),
                )
        elif cls.column_type == 'FixedStrCol':
            return conv.pipe(
                conv.condition(
                    conv.test_isinstance((float, int)),
                    # YAML stores strings containing only digits as numbers.
                    conv.function(unicode),
                    ),
                conv.test_isinstance(basestring),
                conv.test(lambda value: len(value) <= cls.max_length),
                )
        elif cls.column_type == 'FloatCol':
            return conv.pipe(
                conv.test_isinstance((float, int, basestring)),
                conv.make_anything_to_float(accept_expression=True),
                )
        elif cls.column_type == 'IntCol':
            return conv.pipe(
                conv.test_isinstance((int, basestring)),
                conv.make_anything_to_int(accept_expression=True),
                )
        elif cls.column_type == 'StrCol':
            return conv.pipe(
                conv.condition(
                    conv.test_isinstance((float, int)),
                    # YAML stores strings containing only digits as numbers.
                    conv.function(unicode),
                    ),
                conv.test_isinstance(basestring),
                )
        elif cls.column_type == 'AgeCol':
            return conv.pipe(
                conv.test_isinstance((int, basestring)),
                conv.make_anything_to_int(accept_expression=True),
                conv.first_match(
                    conv.test_greater_or_equal(0),
                    conv.test_equals(-9999),
                    ),
                )
        elif cls.column_type == 'EnumCol':
            if not hasattr(cls, 'enum'):
                return conv.pipe(
                    conv.test_isinstance((basestring, int)),
                    conv.anything_to_int,
                    )
            enum = cls.enum
            return conv.pipe(
                conv.test_isinstance((basestring, int)),
                conv.condition(
                    conv.anything_to_int,
                    conv.pipe(
                        # Verify that item index belongs to enumeration.
                        conv.anything_to_int,
                        conv.test_in(enum._vars),
                        ),
                    conv.pipe(
                        # Convert item name to its index.
                        conv.input_to_slug,
                        conv.test_in(cls.index_by_slug),
                        conv.function(lambda slug: cls.index_by_slug[slug]),
                        ),
                    ),
                )


class PersonToEntityColumn(Variable):
    pass


class EntityToPersonColumn(Variable):
    pass


class DatedVariable(Variable):
    pass


def dated_function(start=None, stop=None):
    """Function decorator used to give start & stop instants to a method of a function in class DatedVariable."""
    def dated_function_decorator(function):
        function.start_instant = start
        function.stop_instant = stop
        return function

    return dated_function_decorator


def calculate_output_add(variable, period):
    return variable.calculate(period)


def calculate_output_divide(variable, period):
    return variable.calculate(period)


def set_input_dispatch_by_period(variable, array, period):
    variable.put_in_cache(array, period)

    period_size = period.size
    period_unit = period.unit
    if period_unit == u'year' or period_size > 1:
        after_instant = period.start.offset(period_size, period_unit)
        if period_size > 1:
            sub_period = period.start.period(period_unit)
            while sub_period.start < after_instant:
                existing_array = variable.get_array(sub_period)
                if existing_array is None:
                    variable.put_in_cache(array, sub_period)
                else:
                    # The array of the current sub-period is reused for the next ones.
                    array = existing_array
                sub_period = sub_period.offset(1)
        if period_unit == u'year':
            month = period.start.period(u'month')
            while month.start < after_instant:
                existing_array = variable.get_array(month)
                if existing_array is None:
                    variable.put_in_cache(array, month)
                else:
                    # The array of the current sub-period is reused for the next ones.
                    array = existing_array
                month = month.offset(1)


def set_input_divide_by_period(variable, array, period):
    variable.put_in_cache(array, period)

    period_size = period.size
    period_unit = period.unit
    if period_unit == u'year' or period_size > 1:
        after_instant = period.start.offset(period_size, period_unit)
        if period_size > 1:
            remaining_array = array.copy()
            sub_period = period.start.period(period_unit)
            sub_periods_count = period_size
            while sub_period.start < after_instant:
                existing_array = variable.get_array(sub_period)
                if existing_array is not None:
                    remaining_array -= existing_array
                    sub_periods_count -= 1
                sub_period = sub_period.offset(1)
            if sub_periods_count > 0:
                divided_array = remaining_array / sub_periods_count
                sub_period = period.start.period(period_unit)
                while sub_period.start < after_instant:
                    if variable.get_array(sub_period) is None:
                        variable.put_in_cache(divided_array, sub_period)
                    sub_period = sub_period.offset(1)
        if period_unit == u'year':
            remaining_array = array.copy()
            month = period.start.period(u'month')
            months_count = 12 * period_size
            while month.start < after_instant:
                existing_array = variable.get_array(month)
                if existing_array is not None:
                    remaining_array -= existing_array
                    months_count -= 1
                month = month.offset(1)
            if months_count > 0:
                divided_array = remaining_array / months_count
                month = period.start.period(u'month')
                while month.start < after_instant:
                    if variable.get_array(month) is None:
                        variable.put_in_cache(divided_array, month)
                    month = month.offset(1)
