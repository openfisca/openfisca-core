# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import collections
import datetime
import re

from biryani1 import strings
import numpy as np

from . import conv
from .enumerations import Enum


N_ = lambda message: message
year_or_month_or_day_re = re.compile(ur'(18|19|20)\d{2}(-(0[1-9]|1[0-2])(-([0-2]\d|3[0-1]))?)?$')


# Base Column


class Column(object):
    cerfa_field = None
    consumers = None  # list of prestation names using this column
    default = 0
    dtype = float
    end = None
    entity = None
    formula_constructor = None
    function = None
    info = None
    # json_type = None  # Defined in sub-classes
    label = None
    name = None
    start = None
    survey_only = False
    url = None
    val_type = None

    def __init__(self, cerfa_field = None, default = None, end = None, entity = None, function = None, info = None,
            label = None, start = None, survey_only = False, url = None, val_type = None):
        if cerfa_field is not None:
            self.cerfa_field = cerfa_field
        if default is not None and default != self.default:
            self.default = default
        if end is not None:
            self.end = end
        self.entity = entity or 'ind'
        if function is not None:
            self.function = function
        if info is not None:
            self.info = info
        if label is not None:
            self.label = label
        if start is not None:
            self.start = start
        if survey_only:
            self.survey_only = True
        if url is not None:
            self.url = url
        if val_type is not None and val_type != self.val_type:
            self.val_type = val_type

    def json_default(self):
        return self.default

    def to_json(self):
        self_json = collections.OrderedDict((
            ('@type', self.json_type),
            ))
        if self.cerfa_field is not None:
            self_json['cerfa_field'] = self.cerfa_field
        if self.default is not None:
            self_json['default'] = self.json_default()
        end = self.end
        if end is not None:
            if isinstance(end, datetime.date):
                end = end.isoformat()
            self_json['end'] = end
        if self.entity is not None:
            self_json['entity'] = self.entity
        if self.info is not None:
            self_json['info'] = self.info
        if self.label is not None:
            self_json['label'] = self.label
        if self.name is not None:
            self_json['name'] = self.name
        start = self.start
        if start is not None:
            if isinstance(start, datetime.date):
                start = start.isoformat()
            self_json['start'] = start
        if self.survey_only:
            self_json['survey_only'] = self.survey_only
        if self.url is not None:
            self_json['url'] = self.url
        if self.val_type is not None:
            self_json['val_type'] = self.val_type
        return self_json

    def transform_value_to_json(self, value):
        # Convert a non-NumPy Python value to JSON.
        return value


# Level-1 Columns


class BoolCol(Column):
    '''
    A column of boolean
    '''
    default = False
    dtype = np.bool
    json_type = 'Boolean'

    @property
    def json_to_python(self):
        return conv.pipe(
            conv.test_isinstance((int, bool)),
            conv.anything_to_bool,
            )


class DateCol(Column):
    '''
    A column of Datetime 64 to store dates of people
    '''
    dtype = 'datetime64[D]'
    json_type = 'Date'
    val_type = 'date'

    def json_default(self):
        return unicode(np.array(self.default, self.dtype))  # 0 = 1970-01-01

    @property
    def json_to_python(self):
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
                        conv.test(year_or_month_or_day_re.match, error = N_(u'Invalid year')),
                        conv.function(lambda birth: u'-'.join((birth.split(u'-') + [u'01', u'01'])[:3])),
                        conv.iso8601_input_to_date,
                        ),
                    ),
                ),
            conv.test_between(datetime.date(1870, 1, 1), datetime.date(2099, 12, 31)),
            )

    def transform_value_to_json(self, value):
        # Convert a non-NumPy Python value to JSON.
        return value.isoformat() if value is not None else value


class FloatCol(Column):
    '''
    A column of float 32
    '''
    dtype = np.float32
    json_type = 'Float'

    @property
    def json_to_python(self):
        return conv.pipe(
            conv.test_isinstance((float, int)),
            conv.anything_to_float,
            )


class IntCol(Column):
    '''
    A column of integer
    '''
    dtype = np.int32
    json_type = 'Integer'

    @property
    def json_to_python(self):
        return conv.test_isinstance(int)


class StrCol(Column):
    default = u''
    dtype = object
    json_type = 'String'

    @property
    def json_to_python(self):
        return conv.test_isinstance(basestring)


# Level-2 Columns


class AgeCol(IntCol):
    '''
    A column of Int to store ages of people
    '''
    default = -9999

    @property
    def json_to_python(self):
        return conv.pipe(
            super(AgeCol, self).json_to_python,
            conv.first_match(
                conv.test_greater_or_equal(0),
                conv.test_equals(-9999),
                ),
            )


class EnumCol(IntCol):
    '''
    A column of integer with an enum
    '''
    dtype = np.int16
    enum = None
    index_by_slug = None
    json_type = 'Enumeration'

    def __init__(self, enum = None, **kwargs):
        super(EnumCol, self).__init__(**kwargs)
        if isinstance(enum, Enum):
            self.enum = enum

    @property
    def json_to_python(self):
        enum = self.enum
        if enum is None:
            return conv.pipe(
                conv.test_isinstance((basestring, int)),
                conv.anything_to_int,
                )
        # This converters accepts either an item number or an item name.
        index_by_slug = self.index_by_slug
        if index_by_slug is None:
            self.index_by_slug = index_by_slug = dict(
                (strings.slugify(name), index)
                for index, name in sorted(enum._vars.iteritems())
                )
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
                    conv.test_in(index_by_slug),
                    conv.function(lambda slug: index_by_slug[slug]),
                    ),
                ),
            )

    def to_json(self):
        self_json = super(EnumCol, self).to_json()
        if self.enum is not None:
            self_json['labels'] = collections.OrderedDict(
                (index, label)
                for label, index in self.enum
                )
        return self_json
