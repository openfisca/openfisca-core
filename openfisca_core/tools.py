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


__all__ = [
    'empty_clone',
    'stringify_array',
    'stringify_formula_arguments',
    ]


class Dummy(object):
    """A class that does nothing

    Used by function ``empty_clone`` to create an empty instance from an existing object.
    """
    pass


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


def stringify_formula_arguments(dated_holder_by_variable_name):
    return u', '.join(
        u'{} = {}@{}'.format(
            variable_name,
            variable_dated_holder.entity.key_plural,
            stringify_array(variable_dated_holder.array),
            )
        for variable_name, variable_dated_holder in dated_holder_by_variable_name.iteritems()
        )
