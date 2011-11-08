# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

"""
µSim, Logiciel libre de simulation du système socio-fiscal français
Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul


This file is part of µSim.

    µSim is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    µSim is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with µSim.  If not, see <http://www.gnu.org/licenses/>.
"""

def enum(*enumerated):
    enums = dict(zip(enumerated, range(len(enumerated))))
    enums["names"] = enumerated
    return type('enum', (), enums)
    
from PyQt4.QtXml import QDomDocument
from xml.dom import minidom
from Utils import Bareme
from datetime import datetime
from Config import CONF
import copy


class Tree2Object(object):
    def __init__(self, node, defaut = False):
        for child in node._children:
            setattr(self, child.name(), child)
        for a, b in self.__dict__.iteritems():
            if b.typeInfo() == 'CODE' or b.typeInfo() == 'BAREME':
                if defaut:
                    setattr(self,a, b.default())
                else:
                    setattr(self,a, b.value())
            else:
                setattr(self,a, Tree2Object(b, defaut))

class XmlReader(object):

    def __init__(self, myFile, date = None):
        super(XmlReader, self).__init__()
        self._file = myFile
        self._doc = minidom.parse(self._file)
        self.tree = Node('root')
        if date is None: self._date = datetime.strptime(self._doc.childNodes[0].getAttribute('datesim'),"%Y-%m-%d").date()
        else: self._date = date
        self.handleNodeList(self._doc.childNodes, self.tree)
        self.tree = self.tree.child(0)
        self.param = Tree2Object(self.tree)

    def handleNodeList(self, nodeList, parent):
        for element in nodeList:
            if element.nodeType is not element.TEXT_NODE:
                if element.tagName == "BAREME":
                    code = element.getAttribute('code')
                    desc = element.getAttribute('description')
                    tranches = Bareme(code)
                    for tranche in element.getElementsByTagName("TRANCHE"):
                        seuil = self.handleValues(tranche.getElementsByTagName("SEUIL")[0], self._date)
                        assi = tranche.getElementsByTagName("ASSIETTE")
                        if assi:  assiette = self.handleValues(assi[0], self._date)
                        else: assiette = 1
                        taux  = self.handleValues(tranche.getElementsByTagName("TAUX")[0], self._date)
                        if not seuil is None and not taux is None:
                            tranches.addTranche(seuil, taux*assiette)
                    node = BaremeNode(code, desc, tranches, parent)
                elif element.tagName == "CODE":
                    code = element.getAttribute('code')
                    desc = element.getAttribute('description')
                    myformat = element.getAttribute('format')
                    val = self.handleValues(element, self._date)
                    if not val is None:
                        node = CodeNode(code, desc, float(val), parent, myformat)
                else:
                    code = element.getAttribute('code')
                    desc = element.getAttribute('description')
                    node = Node(code, desc, parent)
                    self.handleNodeList(element.childNodes, node)
    
    def handleValues(self, element, date):
        # TODO gérer les assiettes en mettan l'assiette à 1 si elle n'existe pas
        for val in element.getElementsByTagName("VALUE"):
            deb = datetime.strptime(val.getAttribute('deb'),"%Y-%m-%d").date()
            fin   = datetime.strptime(val.getAttribute('fin'),"%Y-%m-%d").date()
            if deb <= date <= fin:
                return float(val.getAttribute('valeur'))
        return None

class Node(object):
    
    def __init__(self, name, description = '', parent=None):
        
        super(Node, self).__init__()
        
        self._name = name
        self._children = []
        self._description = description
        self._parent = parent
        self._format = 'none' # may take 'none', 'percent', 'int', 'string'
        self._typeInfo = 'NODE'
        
        if parent is not None:
            parent.addChild(self)

    def rmv_empty_code(self):
        to_remove = []
        for child in self._children:
            if not child.hasvalue():
                to_remove.append(child.row())
            else:
                child.rmv_empty_code()
        for indice in reversed(to_remove):
            self.removeChild(indice)

    def asXml(self):
        
        doc = QDomDocument()
        
        node = doc.createElement(self.typeInfo())
        node.setAttribute('datesim', CONF.get('simulation', 'datesim'))
        doc.appendChild(node)
       
        for i in self._children:
            i._recurseXml(doc, node)

        return doc.toString(indent=4)

    def _recurseXml(self, doc, parent):
        if self.isdirty():
            node = doc.createElement(self.typeInfo())
            parent.appendChild(node)
    
            node.setAttribute('code', self.name())
            node.setAttribute('description', self.description())
    
            for i in self._children:
                i._recurseXml(doc, node)

    def load(self, other):
        for child in other._children:
            for mychild in self._children:
                if mychild.name() == child.name():
                    mychild.load(child)

    def name(self):
        return self._name

    def typeInfo(self):
        return self._typeInfo
    
    def format(self):
        return self._format

    def hasvalue(self):
        hasvalue = False
        for child in self._children:
            hasvalue = hasvalue or child.hasvalue()
        return hasvalue
    
    def isdirty(self):
        '''
        Check if a value has been changed in a child object
        '''
        dirty = False
        for child in self._children:
            dirty = dirty or child.isdirty()
        return dirty
            
    def description(self):
        return self._description

    def addChild(self, child):
        self._children.append(child)
        child._parent = self

    def insertChild(self, position, child):
        
        if position < 0 or position > len(self._children):
            return False
        
        self._children.insert(position, child)
        child._parent = self
        return True

    def removeChild(self, position):
        
        if position < 0 or position > len(self._children):
            return False
        
        child = self._children.pop(position)
        child._parent = None

        return True

    def child(self, row):
        return self._children[row]
    
    def childCount(self):
        return len(self._children)

    def parent(self):
        return self._parent
    
    def row(self):
        if self._parent is not None:
            return self._parent._children.index(self)

    def log(self, tabLevel=-1):
        output     = ""
        tabLevel += 1
        
        for i in range(tabLevel):
            output += "\t"
        
        output += "|------" + self._name + "\n"
        
        for child in self._children:
            output += child.log(tabLevel)
        
        tabLevel -= 1
        output += "\n"
        
        return output

    def __repr__(self):
        return self.log()

    def data(self, column):        
        if   column is 0: return self.description()
    
    def setData(self, column, value):
        if   column is 0: pass
    
    def resource(self):
        return None

class CodeNode(Node):
    
    def __init__(self, name, description, value, parent, myformat = 'none'):
        super(CodeNode, self).__init__(name, description, parent)
        self._value = value
        self._default = value
        self._typeInfo = 'CODE'
        self._format = myformat

    def _recurseXml(self, doc, parent):
        if self.isdirty():
            node = doc.createElement(self.typeInfo())
            parent.appendChild(node)
    
            node.setAttribute('code', self.name())
            node.setAttribute('description', self.description())
    
            val = doc.createElement('VALUE')
            node.appendChild(val)
            val.setAttribute('valeur', '%f' % self.value())
            date = CONF.get('simulation', 'datesim')
            val.setAttribute('deb', date)
            val.setAttribute('fin', date)

    def log(self, tabLevel=-1):
        output     = ""
        tabLevel += 1
        
        for i in range(tabLevel):
            output += "\t"
        
        output += "|------" + self._name + ' : ' + str(self._value) + "\n"
        
        for child in self._children:
            output += child.log(tabLevel)
        
        tabLevel -= 1
        output += "\n"
        
        return output

    def load(self, other):
        self._value = other.value()

    def value(self):
        return self._value

    def default(self):
        return self._default

    def hasvalue(self):
        if self._value is None:
            return False
        return True
    
    def isdirty(self):
        if self._value == self._default:
            return False
        return True
        
    def data(self, column):
        r = super(CodeNode, self).data(column)        
        if   column is 1: r = self.default()
        if   column is 2: r = self.value()
        return r

    def setData(self, column, value):
        super(CodeNode, self).setData(column, value)        
        if   column is 1: pass
        elif column is 2: self._value = value.toPyObject()

class BaremeNode(Node):
    
    def __init__(self, name, description, value, parent):
        super(BaremeNode, self).__init__(name, description, parent)
        self._value = value
        self._default = copy.deepcopy(value)
        self._typeInfo = 'BAREME'

    def _recurseXml(self, doc, parent):
        if self.isdirty():
            node = doc.createElement(self.typeInfo())
            parent.appendChild(node)
    
            node.setAttribute('code', self.name())
            node.setAttribute('description', self.description())
            bareme = self._value
            S = bareme.seuils
            T = bareme.taux
            date = CONF.get('simulation', 'datesim')

            for i in range(self._value.getNb()):
                tranche = doc.createElement('TRANCHE')
                tranche.setAttribute('code', 'tranche%d' % i)
                node.appendChild(tranche)
    
                seuil = doc.createElement('SEUIL')
                tranche.appendChild(seuil)
                val = doc.createElement('VALUE')
                seuil.appendChild(val)
                val.setAttribute('valeur', '%f' % S[i])
                val.setAttribute('deb', date)
                val.setAttribute('fin', date)
    
                taux = doc.createElement('TAUX')
                tranche.appendChild(taux)
                val = doc.createElement('VALUE')
                taux.appendChild(val)
                val.setAttribute('valeur', '%f' % T[i])
                val.setAttribute('deb', date)
                val.setAttribute('fin', date)

    def value(self):
        return self._value
    
    def default(self):
        return self._default

    def load(self, other):
        self._value = other.value()
        
    def data(self, column):
        r = super(BaremeNode, self).data(column)        
        if   column is 1: r = self.value()
        return r
    
    def setData(self, column, value):
        pass
        
    def hasvalue(self):
        return True
    
    def isdirty(self):
        if self._value == self._default:
            return False
        return True
    
    