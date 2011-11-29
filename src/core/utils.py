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
from Utils import OutNode
from xml.dom import minidom


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

def handleXml(doc, tree, model):
    if doc.childNodes:
        for element in doc.childNodes:
            if element.nodeType is not element.TEXT_NODE:
                code = element.getAttribute('code')
                desc = element.getAttribute('desc')
                cols = element.getAttribute('color')
                short = element.getAttribute('shortname')
                typv = element.getAttribute('typevar')
                if cols is not '':
                    a = cols.rsplit(',')
                    col = (float(a[0]), float(a[1]), float(a[2]))
                else: col = (0,0,0)
                if typv is not '':
                    typv = int(typv)
                else: typv = 0
                child = OutNode(code, desc, color = col, typevar = typv, shortname=short)
                tree.addChild(child)
                handleXml(element, child, model)
    else:
        val = getattr(model, tree.code).get_value()
        tree.setVals(val)
            

def gen_output_data(model):


#        nbenfmax = table.nbenfmax 
#        enfants = ['enf%d' % i for i in range(1, nbenfmax+1)]
#        self.members = ['pref', 'cref'] + enfants

    _doc = minidom.parse('data/totaux.xml')
    tree = OutNode('root', 'root')

    handleXml(_doc, tree, model)

#        nb_uci = self.UC(table)
    
#        nivvie = OutNode('nivvie', 'Niveau de vie', shortname = 'Niveau de vie', vals = tree['revdisp'].vals/nb_uci, typevar = 2, parent= tree)
#        tree.addChild(nivvie)
#        table.close_()
    return tree

