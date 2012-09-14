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
    
from xml.etree.ElementTree import ElementTree, SubElement, Element
from xml.dom import minidom
from core.utils import Bareme
from datetime import datetime
from Config import CONF

class Tree2Object(object):
    def __init__(self, node, defaut = False):
        for child in node._children:
            setattr(self, child.code, child)
        for a, b in self.__dict__.iteritems():
            if b.typeInfo == 'CODE' or b.typeInfo == 'BAREME':
                if defaut:
                    setattr(self,a, b.default)
                else:
                    setattr(self,a, b.value)
            else:
                setattr(self,a, Tree2Object(b, defaut))

class XmlReader2(object):
    def __init__(self, paramFile, date = None):
        super(XmlReader, self).__init__()
        self._doc = minidom.parse(paramFile)        
        self.tree = Node('root')
        if date is None: self._date = datetime.strptime(self._doc.childNodes[0].getAttribute('datesim'),"%Y-%m-%d").date()
        else: self._date = date
        self.handleNodeList(self._doc.childNodes, self.tree)
        self.tree = self.tree.child(0)
        self.param = Tree2Object(self.tree)

class XmlReader(object):
    def __init__(self, paramFile, date = None):
        super(XmlReader, self).__init__()
        self._doc = minidom.parse(paramFile)        
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
                    option = element.getAttribute('option')
                    tranches = Bareme(code)
                    tranches.setOption(option)
                    for tranche in element.getElementsByTagName("TRANCHE"):
                        seuil = self.handleValues(tranche.getElementsByTagName("SEUIL")[0], self._date)
                        assi = tranche.getElementsByTagName("ASSIETTE")
                        if assi:  assiette = self.handleValues(assi[0], self._date)
                        else: assiette = 1
                        taux  = self.handleValues(tranche.getElementsByTagName("TAUX")[0], self._date)
                        if not seuil is None and not taux is None:
                            tranches.addTranche(seuil, taux*assiette)
                    tranches.marToMoy()
                    node = BaremeNode(code, desc, tranches, parent)
                elif element.tagName == "CODE":
                    code = element.getAttribute('code')
                    desc = element.getAttribute('description')
                    valueFormat = element.getAttribute('format')
                    val = self.handleValues(element, self._date)
                    if not val is None:
                        node = CodeNode(code, desc, float(val), parent, valueFormat)
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
    def __init__(self, code, description = '', parent=None):        
        super(Node, self).__init__()
        self._parent = parent
        self._children = []

        self.code = code
        self.description = description
        self.valueFormat = 'none'
        self.typeInfo = 'NODE'
        
        if parent is not None:
            parent.addChild(self)

    def rmv_empty_code(self):
        to_remove = []
        for child in self._children:
            if not child.hasValue():
                to_remove.append(child.row())
            else:
                child.rmv_empty_code()
        for indice in reversed(to_remove):
            self.removeChild(indice)

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

    def asXml(self, fileName):
        doc = ElementTree()
        root = Element(tag = self.typeInfo, 
                       attrib={'datesim': CONF.get('simulation', 'datesim')})

        for i in self._children:
            i._recurseXml(root)

        doc._setroot(root)
        return doc.write(fileName, encoding = "utf-8", method = "xml")

    def _recurseXml(self, parent):
        if self.isDirty():
            child = SubElement(parent, 
                               tag = self.typeInfo,
                               attrib = {'code': self.code,
                                         'description': self.description})
            
            for i in self._children:
                i._recurseXml(child)

    def load(self, other):
        for child in other._children:
            for mychild in self._children:
                if mychild.code == child.code:
                    mychild.load(child)

    def getCode(self):
        return self._code

    def setCode(self, value):
        self._code = value

    code = property(getCode, setCode)
    
    def getType(self):
        return self._typeInfo

    def setType(self, value):
        self._typeInfo = value

    typeInfo = property(getType, setType)
    
    def getDescription(self):
        return self._description

    def setDescription(self, value):
        self._description = value
        
    description = property(getDescription, setDescription)

    def getValueFormat(self):
        return self._format

    def setValueFormat(self, value):
        if not value in ('none', 'integer', 'percent'):
            return Exception("Unknowned %s valueFormat: valueFormat can be 'none', 'integer', 'percent'" % value)
        self._format = value
    
    valueFormat = property(getValueFormat, setValueFormat)

    def getValue(self):
        return self._value

    def setValue(self, value):
        self._value = value

    value = property(getValue, setValue)

    def getDefault(self):
        return self._default

    def setDefault(self, value):
        self._default = value
        
    default = property(getDefault, setDefault)

    def hasValue(self):
        out = False
        for child in self._children:
            out = out or child.hasValue()
        return out
    
    def isDirty(self):
        '''
        Check if a value has been changed in a child object
        '''
        dirty = False
        for child in self._children:
            dirty = dirty or child.isDirty()
        return dirty
            

    def addChild(self, child):
        self._children.append(child)
        child._parent = self

    def child(self, row):
        return self._children[row]
    
    def childCount(self):
        return len(self._children)

    def parent(self):
        return self._parent
    
    def row(self):
        if self._parent is not None:
            return self._parent._children.index(self)

    def data(self, column):        
        if column is 0: return self.description
    
    def setData(self, column, value):
        if column is 0: pass
    
class CodeNode(Node):
    def __init__(self, code, description, value, parent, valueFormat = 'none'):
        super(CodeNode, self).__init__(code, description, parent)
        self.value = value
        self.default = value
        self.typeInfo = 'CODE'
        self.valueFormat = valueFormat

    def _recurseXml(self, parent):
        if self.isDirty():
            child = SubElement(parent, 
                               tag = self.typeInfo,
                               attrib = {'code': self.code,
                                         'description': self.description})

            date = CONF.get('simulation', 'datesim')
            SubElement(child, 
                       tag = 'VALUE', 
                       attrib = {'valeur': '%f' % self.value,
                                 'deb': date,
                                 'fin': date})

    def load(self, other):
        self.value = other.value

    def hasValue(self):
        if self.value is None:
            return False
        return True
    
    def isDirty(self):
        if self.value == self.default:
            return False
        return True
        
    def data(self, column):
        r = super(CodeNode, self).data(column)        
        if   column is 1: r = self.default
        if   column is 2: r = self.value
        return r

    def setData(self, column, value):
        super(CodeNode, self).setData(column, value)        
        if   column is 1: pass
        elif column is 2: self.value = value.toPyObject()

class BaremeNode(Node):
    
    def __init__(self, code, description, value, parent):
        super(BaremeNode, self).__init__(code, description, parent)
        self.value = value
        # create a copy of the default value by hand
        self.default = Bareme(value._name, option = value.option)
        for s , t in value._tranches:
            self.default.addTranche(s, t)
        self.default.marToMoy()
        self.typeInfo = 'BAREME'

    def _recurseXml(self, parent):
        if self.isDirty():
            child = SubElement(parent, 
                               tag = self.typeInfo,
                               attrib = {'code': self.code,
                                         'description': self.description})


    
            bareme = self.value
            S = bareme.seuils
            T = bareme.taux
            date = CONF.get('simulation', 'datesim')

            for i in range(self.value.getNb()):
                tranche = SubElement(child, 
                                     tag = 'TRANCHE', 
                                     attrib = {'code': 'tranche%d' % i})

                seuil = SubElement(tranche, 
                                     tag = 'SEUIL', 
                                     attrib = {'code': 'tranche%d' % i})

                SubElement(seuil, 
                           tag = 'VALUE', 
                           attrib = {'valeur': '%f' % S[i],
                                     'deb': date,
                                     'fin': date})

                taux = SubElement(tranche, 
                                     tag = 'TAUX')

                SubElement(taux, 
                           tag = 'VALUE', 
                           attrib = {'valeur': '%f' % T[i],
                                     'deb': date,
                                     'fin': date})
                                 
    def load(self, other):
        self.value = other.value
        
    def data(self, column):
        r = super(BaremeNode, self).data(column)        
        if   column is 1: r = self.value
        return r
    
    def setData(self, column, value):
        pass
        
    def hasValue(self):
        return True
    
    def isDirty(self):
        if self.value._tranches == self.default._tranches:
            return False
        return True
    
    