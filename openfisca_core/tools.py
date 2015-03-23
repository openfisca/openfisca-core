# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
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


import numpy as np


__all__ = [
    'assert_near',
    'empty_clone',
    'stringify_array',
    ]


class Dummy(object):
    """A class that does nothing

    Used by function ``empty_clone`` to create an empty instance from an existing object.
    """
    pass


def assert_near(value, target_value, absolute_error_margin = 0, message = '', relative_error_margin = None):
    assert absolute_error_margin is not None or relative_error_margin is not None
    if isinstance(value, (list, tuple)):
        value = np.array(value)
    if isinstance(target_value, (list, tuple)):
        target_value = np.array(target_value)
    if isinstance(message, unicode):
        message = message.encode('utf-8')
    if isinstance(value, np.ndarray):
        if absolute_error_margin is not None:
            assert (abs(target_value - value) <= absolute_error_margin).all(), \
                '{}{} differs from {} with an absolute margin {} > {}'.format(message, value, target_value,
                    abs(target_value - value), absolute_error_margin)
        if relative_error_margin is not None:
            assert (abs(target_value - value) <= abs(relative_error_margin * target_value)).all(), \
                '{}{} differs from {} with a relative margin {} > {}'.format(message, value, target_value,
                    abs(target_value - value), abs(relative_error_margin * target_value))
    else:
        if absolute_error_margin is not None:
            assert abs(target_value - value) <= absolute_error_margin, \
                '{}{} differs from {} with an absolute margin {} > {}'.format(message, value, target_value,
                    abs(target_value - value), absolute_error_margin)
        if relative_error_margin is not None:
            assert abs(target_value - value) <= abs(relative_error_margin * target_value), \
                '{}{} differs from {} with a relative margin {} > {}'.format(message, value, target_value,
                    abs(target_value - value), abs(relative_error_margin * target_value))


def empty_clone(original):
    """Create a new empty instance of the same class of the original object."""
    new = Dummy()
    new.__class__ = original.__class__
    return new


def stringify_array(array):
    """Generate a clean string representation of a NumPY array.

    This function exists, because str(array) sucks for logs, etc.
    """
    return u'[{}]'.format(u', '.join(
        unicode(cell)
        for cell in array
        )) if array is not None else u'None'
