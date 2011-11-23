# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

"""
openFisca, Logiciel libre de simulation du système socio-fiscal français
Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

This file is part of openFisca.

    openFisca is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    openFisca is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with openFisca.  If not, see <http://www.gnu.org/licenses/>.
"""
from __future__ import division

class Enum(object):
    def __init__(self, varlist):
        self._vars = {}
        self._count = 0
        for var in varlist:
            self._vars.update({self._count:var})
            self._count += 1
        for key, var in self._vars.iteritems():
            setattr(self, var, key)
            
    def __getitem__(self, var):
        return getattr(self, var)

    def __iter__(self):
        return self.itervars()
    
    def itervars(self):
        for key, val in self._vars.iteritems():
            yield (val, key)
            
    def itervalues(self):
        for val in self._vars:
            yield val
