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


from __future__ import division

import collections
from datetime import date

from biryani1 import strings
import numpy as np

from . import conv
from .enumerations import Enum


def default_frequency_converter(from_ = None, to_ = None):
    """
    Default function to convert Columns between different frequencies
    """
    if (from_ is None) and (to_ is None):
        return lambda x: x

    if (from_ == "year") and (to_ == "trim"):
        return lambda x: x / 4

    if (from_ == "trim") and (to_ == "year"):
        return lambda x: x * 4

    if (from_ == "year") and (to_ == "month"):
        return lambda x: x / 12

    if (from_ == "month") and (to_ == "year"):
        return lambda x: 12 * x


# Base Column


class Column(object):
    _default = 0
    _dtype = float
    _frequency_converter = default_frequency_converter
    end = None
    entity = None
    freq = None
    # json_type = None  # Defined in sub-classes
    label = None
    legislative_input = False
    name = None
    start = None
    survey_only = False
    val_type = None

    def __init__(self, label = None, default = None, entity = None, start = None, end = None, val_type = None,
            freq = None, legislative_input = True, survey_only = False):
        if default is not None and default != self._default:
            self._default = default
        if end is not None:
            self.end = end
        self.entity = entity or 'ind'
        self.freq = freq or 'year'
        if label is not None:
            self.label = label
        if legislative_input:
            self.legislative_input = True
        if start is not None:
            self.start = start
        if survey_only:
            self.survey_only = True
        if val_type is not None and val_type != self.val_type:
            self.val_type = val_type

    def to_json(self):
        self_json = collections.OrderedDict((
            ('@type', self.json_type),
            ))
        if self._default is not None:
            self_json['default'] = self._default
        end = self.end
        if end is not None:
            if isinstance(end, date):
                end = end.isoformat()
            self_json['end'] = end
        if self.entity is not None:
            self_json['entity'] = self.entity
        if self.freq != 'year':
            self_json['freq'] = self.freq
        if self.label is not None:
            self_json['label'] = self.label
        if self.name is not None:
            self_json['name'] = self.name
        start = self.start
        if start is not None:
            if isinstance(start, date):
                start = start.isoformat()
            self_json['start'] = start
        if self.val_type is not None:
            self_json['val_type'] = self.val_type
        return self_json


# Level-1 Columns


class BoolCol(Column):
    '''
    A column of boolean
    '''
    _default = False
    _dtype = np.bool
    json_type = 'Boolean'

    @property
    def json_to_python(self):
        return conv.pipe(
            conv.test_isinstance(int, bool),
            conv.anything_to_bool,
            conv.default(self._default),
            )


class DateCol(Column):
    '''
    A column of Datetime 64 to store dates of people
    '''
    _dtype = np.datetime64
    json_type = 'Date'
    val_type = 'date'

    @property
    def json_to_python(self):
        return conv.pipe(
            conv.test_isinstance(basestring),
            conv.iso8601_input_to_date,
            conv.default(self._default),
            )


class FloatCol(Column):
    '''
    A column of float 32
    '''
    _dtype = np.float32
    json_type = 'Float'

    @property
    def json_to_python(self):
        return conv.pipe(
            conv.test_isinstance(float, int),
            conv.anything_to_float,
            conv.default(self._default),
            )


class IntCol(Column):
    '''
    A column of integer
    '''
    _dtype = np.int32
    json_type = 'Integer'

    @property
    def json_to_python(self):
        return conv.pipe(
            conv.test_isinstance(int),
            conv.default(self._default),
            )


# Level-2 Columns


class AgesCol(IntCol):
    '''
    A column of Int to store ages of people
    '''
    _default = -9999

    @property
    def json_to_python(self):
        return conv.pipe(
            super(AgesCol, self).json_to_python,
            conv.first_match(
                conv.test_greater_or_equal(0),
                conv.test_equals(-9999),
                ),
            )


class EnumCol(IntCol):
    '''
    A column of integer with an enum
    '''
    _dtype = np.int16
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
                conv.default(self._default),
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
            conv.default(
                self._default
                if self._default is not None and self._default in enum._nums
                else min(enum._vars.iterkeys())
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


# Base Prestation


class Prestation(Column):
    """
    Prestation is a wraper around a function which takes some arguments and return a single array.
    _P is a reserved kwargs intended to pass a tree of parametres to the function
    """
    _children = None
    _freq = None  # Caution: Not the same as Column.freq
    _func = None
    _has_freq = False
    _hasOption = False
    _needDefaultParam = False
    _needParam = False
    _option = None
    _parents = None
    calculated = False
    disabled = False
    inputs = None
    json_type = 'Float'

    def __init__(self, func, entity = None, label = None, start = None, end = None, val_type = None, freq = None, survey_only = False):
        super(Prestation, self).__init__(label = label, entity = entity, start = start, end = end, val_type = val_type,
            freq = freq, survey_only = survey_only)

        self._children = set()  # prestations immediately affected by current prestation
        self._freq = {}
        assert func is not None, 'A function to compute the prestation should be provided'
        self._func = func
        self._option = {}
        self._parents = set()  # prestations that current prestations depends on
        self.inputs = set(func.__code__.co_varnames[:func.__code__.co_argcount])

        # Check if function func needs parameter tree _P.
        if '_P' in self.inputs:
            self._needParam = True
            self.inputs.remove('_P')

        # Check if function func needs default parameter tree _defaultP.
        if '_defaultP' in self.inputs:
            self._needDefaultParam = True
            self.inputs.remove('_defaultP')

        # Check if an option dict is passed to the function.
        if '_option' in self.inputs:
            self._hasOption = True
            self.inputs.remove('_option')
            self._option = func.func_defaults[0]
            for var in self._option:
                assert var in self.inputs, '%s in option but not in function args' % var

        # Check if a frequency dict is passed to the function.
        if '_freq' in self.inputs:
            self._has_freq = True
            self.inputs.remove('_freq')
            if self._hasOption:
                self._freq = func.func_defaults[1]
            else:
                self._freq = func.func_defaults[0]
            for var in self._freq:
                assert var in self.inputs, '%s in freq but not in function args' % var

    def add_child(self, prestation):
        self._children.add(prestation)
        prestation._parents.add(self)

    def to_column(self):
        col = Column(label = self.label,
                     entity = self.entity,
                     start = self.start,
                     end = self.end,
                     val_type = self.val_type,
                     freq = self.freq)
        col.name = self.name
        return col


# Level-1 Prestations


class BoolPresta(Prestation, BoolCol):
    '''
    A Prestation inheriting from BoolCol
    '''
    def __init__(self, func, **kwargs):
        BoolCol.__init__(self, **kwargs)
        Prestation.__init__(self, func = func, **kwargs)


class EnumPresta(Prestation, EnumCol):
    '''
    A Prestation inheriting from EnumCol
    '''
    def __init__(self, func, enum = None, **kwargs):
        EnumCol.__init__(self, enum = enum, **kwargs)
        Prestation.__init__(self, func, **kwargs)


class IntPresta(Prestation, IntCol):
    '''
    A Prestation inheriting from IntCol
    '''
    def __init__(self, func, **kwargs):
        IntCol.__init__(self, **kwargs)
        Prestation.__init__(self, func, **kwargs)


#    def dep_resolve(self, resolved=set(), unresolved=set()):
#        '''
#        Dependency solver.
#        Algorithm found here http://www.electricmonk.nl/log/2008/08/07/dependency-resolving-algorithm/
#        '''
#        edges = self._parents
#        unresolved.add(self)
#        for edge in edges:
#            if edge not in resolved:
#                if edge in unresolved:
#                    raise Exception('Circular reference detected: %s -> %s' % (self._name, edge._name))
#                edge.dep_resolve(resolved, unresolved)
#
#        resolved.add(self)
#        unresolved.remove(self)
