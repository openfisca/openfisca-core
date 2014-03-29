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


class Accessor(object):
    """Access to attributes of attributes of... of a root object.

    May be used to access inside a legislation tree or...
    """
    name = None
    parent = None

    def __init__(self, name = None, parent = None):
        if name is None:
            assert parent is None
        else:
            self.name = name
            if parent is not None:
                self.parent = parent

    def __call__(self, legislation, default = UnboundLocalError):
        parent = self.parent
        if parent is not None:
            legislation = parent(legislation, default = default)
        name = self.name
        if name is None or legislation is default:
            return legislation
        return getattr(legislation, self.name) \
            if default is UnboundLocalError \
            else getattr(legislation, self.name, default)

    def __getattribute__(self, name):
        if name.startswith('__') or name in ('iter_ancestors', 'name', 'parent'):
            return super(Accessor, self).__getattribute__(name)
        return Accessor(name = name, parent = self if super(Accessor, self).__getattribute__('name') is not None else None)
            
    def __str__(self):
        return 'Accessor({})'.format('.'.join(
            ancestor.name
            for ancestor in reversed(list(self.iter_ancestors()))
            ))

    def iter_ancestors(self, skip_self = False):
        if not skip_self:
            yield self
        parent = self.parent
        if parent is not None:
            for ancestor in parent.iter_ancestors():
                yield ancestor


law = Accessor()
