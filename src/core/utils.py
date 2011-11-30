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

def handle_output_xml(doc, tree, model, unit = 'men'):
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
                handle_output_xml(element, child, model)
    else:
        idx = model._index[unit]
        inputs = model._inputs
        enum = getattr(inputs, 'qui'+unit).enum
        people = [x[1] for x in enum]
        if hasattr(model, tree.code):
            model.calculate(tree.code)
            val = getattr(model, tree.code).get_value(idx, opt = people, sum_ = True)
        elif hasattr(inputs, tree.code):
            val = getattr(inputs, tree.code).get_value(idx, opt = people, sum_ = True)
        else:
            raise Exception('%s was not find in model nor in inputs' % tree.code)
        tree.setVals(val)
            
def gen_output_data(model):

#        nbenfmax = table.nbenfmax 
#        enfants = ['enf%d' % i for i in range(1, nbenfmax+1)]
#        self.members = ['pref', 'cref'] + enfants

    _doc = minidom.parse('data/totaux.xml')
    tree = OutNode('root', 'root')

    handle_output_xml(_doc, tree, model)

#        nb_uci = self.UC(table)
    
#        nivvie = OutNode('nivvie', 'Niveau de vie', shortname = 'Niveau de vie', vals = tree['revdisp'].vals/nb_uci, typevar = 2, parent= tree)
#        tree.addChild(nivvie)

    return tree

class OutNode(object):
    def __init__(self, code, desc, shortname = '', vals = 0, color = (0,0,0), typevar = 0, parent = None):
        self.parent = parent
        self.children = []
        self.code = code
        self.desc = desc
        self.color = color
        self.visible = 0
        self.typevar = typevar
        self._vals = vals
        self._taille = 0
        if shortname: self.shortname = shortname
        else: self.shortname = code
        
    def addChild(self, child):
        self.children.append(child)
        if child.color == (0,0,0):
            child.color = self.color
        child.setParent(self)

    def setParent(self, parent):
        self.parent = parent

    def child(self, row):
        return(self.children[row])

    def childCount(self):
        return len(self.children)

    def row(self):
        if self.parent is not None:
            return self.parent.children.index(self)

    def setLeavesVisible(self):
        for child in self.children:
            child.setLeavesVisible()
        if (self.children and (self.code !='revdisp')) or (self.code == 'nivvie'):
            self.visible = 0
        else:
            self.visible = 1
    
    def partiallychecked(self):
        if self.children:
            a = True
            for child in self.children:
                a = a and (child.partiallychecked() or child.visible)
            return a
        return False
    
    def hideAll(self):
        if self.code == 'revdisp':
            self.visible = 1
        else:
            self.visible = 0
        for child in self.children:
            child.hideAll()
    
    def setHidden(self, changeParent = True):
        # les siblings doivent être dans le même
        if self.partiallychecked():
            self.visible = 0
            return
        for sibling in self.parent.children:
            sibling.visible = 0
            for child in sibling.children:
                child.setHidden(False)
        if changeParent:
            self.parent.visible = 1
                    
    def setVisible(self, changeSelf = True, changeParent = True):
        if changeSelf:
            self.visible = 1
        if self.parent is not None:
            for sibling in self.parent.children:
                if not (sibling.partiallychecked() or sibling.visible ==1):
                    sibling.visible = 1
            if changeParent:
                self.parent.setVisible(changeSelf = False)


    def getVals(self):
        return self._vals

    def setVals(self, vals):
        dif = vals - self._vals
        self._vals = vals
        self._taille = len(vals)
        if self.parent:
            self.parent.setVals(self.parent.vals + dif)
    
    vals = property(getVals, setVals)
        
    def __getitem__(self, key):
        if self.code == key:
            return self
        for child in self.children:
            val = child[key]
            if not val is None:
                return val
    
    def log(self, tabLevel=-1):
        output     = ""
        tabLevel += 1
        
        for i in range(tabLevel):
            output += "\t"
        
        output += "|------" + self.code + "\n"
        
        for child in self.children:
            output += child.log(tabLevel)
        
        tabLevel -= 1
        output += "\n"
        
        return output

    def __repr__(self):
        return self.log()

    def difference(self, other):
        self.vals -=  other.vals
        for child in self.children:
            child.difference(other[child.code])

    def __iter__(self):
        return self.inorder()
    
    def inorder(self):
        for child in self.children:
            for x in child.inorder():
                yield x
        yield self
