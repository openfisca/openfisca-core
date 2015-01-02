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


class Enum(object):
    def __init__(self, varlist, start = 0):
        self._vars = {}
        self._nums = {}
        self._count = 0
        for var in varlist:
            self._vars.update({self._count + start: var})
            self._nums.update({var: self._count + start})
            self._count += 1

    def __getitem__(self, var):
        return self._nums[var]

    def __iter__(self):
        return self.itervars()

    def __len__(self):
        return self._count

    def itervars(self):
        for key, val in self._vars.iteritems():
            yield (val, key)

    def itervalues(self):
        for val in self._vars:
            yield val
