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


from datetime import datetime
from xml.dom import minidom
from xml.etree.ElementTree import Element, ElementTree, SubElement

from .taxscales import TaxScale

class Tree2Object(object):
    def __init__(self, node, defaut = False):
        for child in node._children:
            setattr(self, child.code, child)
        for a, b in self.__dict__.iteritems():
            if b.type_info == 'CODE' or b.type_info == 'BAREME':
                if defaut:
                    setattr(self, a, b.default)
                else:
                    setattr(self, a, b.value)
            else:
                setattr(self,a, Tree2Object(b, defaut))


class XmlReader(object):
    def __init__(self, paramFile, date = None):
        super(XmlReader, self).__init__()
        self._doc = minidom.parse(paramFile)
        self.tree = Node('root')
        if date is None:
            self._date = datetime.strptime(self._doc.childNodes[0].getAttribute('datesim'),"%Y-%m-%d").date()
        else:
            self._date = date
        self.handleNodeList(self._doc.childNodes, self.tree)
        self.tree = self.tree.child(0)

    def handleNodeList(self, nodeList, parent):
        for element in nodeList:
            if element.nodeType is not element.TEXT_NODE and element.nodeType is not element.COMMENT_NODE:
                if element.tagName == "BAREME":
                    code = element.getAttribute('code')
                    desc = element.getAttribute('description')
                    option = element.getAttribute('option')
                    value_type   = element.getAttribute('type')
                    tax_scale = TaxScale(code)
                    tax_scale.set_option(option)
                    for tranche in element.getElementsByTagName("TRANCHE"):
                        seuil = self.handleValues(tranche.getElementsByTagName("SEUIL")[0], self._date)
                        assi = tranche.getElementsByTagName("ASSIETTE")
                        if assi:  assiette = self.handleValues(assi[0], self._date)
                        else: assiette = 1
                        taux  = self.handleValues(tranche.getElementsByTagName("TAUX")[0], self._date)
                        if not seuil is None and not taux is None:
                            tax_scale.add_bracket(seuil, taux*assiette)
                    tax_scale.marginal_to_average()
                    node = BaremeNode(code, desc, tax_scale, parent, value_type)
                elif element.tagName == "CODE":
                    code = element.getAttribute('code')
                    desc = element.getAttribute('description')
                    value_format = element.getAttribute('format')
                    value_type   = element.getAttribute('type')
                    val = self.handleValues(element, self._date)
                    if not val is None:
                        node = CodeNode(code, desc, float(val), parent, value_format, value_type)
                else:
                    code = element.getAttribute('code')
                    desc = element.getAttribute('description')
                    node = Node(code, desc, parent)
                    self.handleNodeList(element.childNodes, node)

    def handleValues(self, element, date):
        # TODO gérer les assiettes en mettan l'assiette à 1 si elle n'existe pas
        for val in element.getElementsByTagName("VALUE"):
            try:
                deb = datetime.strptime(val.getAttribute('deb'),"%Y-%m-%d").date()
                fin   = datetime.strptime(val.getAttribute('fin'),"%Y-%m-%d").date()
                if deb <= date <= fin:
                    return float(val.getAttribute('valeur'))
            except Exception, e:
                code = element.getAttribute('code')
                raise Exception("Problem error when dealing with %s : \n %s" %(code,e))
        return None


class Node(object):
    def __init__(self, code, description = '', parent=None):
        super(Node, self).__init__()
        self._parent = parent
        self._children = []

        self.code = code
        self.description = description
        self.value_format = None
        self.value_type = None
        self.type_info = 'NODE'

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

    def asXml(self, fileName, datesim):
        doc = ElementTree()
        root = Element(tag = self.type_info,
                       attrib={'datesim': datesim})

        for i in self._children:
            i._recurseXml(root, datesim)

        doc._setroot(root)
        return doc.write(fileName, encoding = "utf-8", method = "xml")

    def _recurseXml(self, parent, datesim):
        if self.isDirty():
            child = SubElement(parent,
                               tag = self.type_info,
                               attrib = {'code': self.code,
                                         'description': self.description})

            for i in self._children:
                i._recurseXml(child, datesim)

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
        return self._type_info

    def setType(self, value):
        self._type_info = value

    type_info = property(getType, setType)

    def getDescription(self):
        return self._description

    def setDescription(self, value):
        self._description = value

    description = property(getDescription, setDescription)

    def getValueFormat(self):
        return self._format

    def setValueFormat(self, value):
        if not value in (None, 'integer', 'percent'):
            return Exception("Unknowned %s value_format: value_format can be None, 'integer', 'percent'" % value)
        self._format = value

    value_format = property(getValueFormat, setValueFormat)

    def getValueType(self):
        return self._type

    def setValueType(self, value):
        type_list = (None, 'monetary', 'age', 'hours', 'days', 'years')
        if not value in type_list:
            return Exception("Unknowned %s value_type: value_type can be None, 'monetary', 'age', 'hours', 'days', 'years'" % value)
        self._type = value

    value_type = property(getValueType, setValueType)


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
    def __init__(self, code, description, value, parent, value_format = None, value_type = None):
        super(CodeNode, self).__init__(code, description, parent)
        self.value = value
        self.default = value
        self.type_info = 'CODE'
        self.value_format = value_format
        self.value_type = value_type

    def _recurseXml(self, parent, datesim):
        if self.isDirty():
            child = SubElement(parent,
                               tag = self.type_info,
                               attrib = {'code': self.code,
                                         'description': self.description})

            SubElement(child,
                       tag = 'VALUE',
                       attrib = {'valeur': '%f' % self.value,
                                 'deb': datesim,
                                 'fin': datesim})

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
        if column is 1:
            r = self.default
        if column is 2:
            r = self.value
        return r

    def setData(self, column, value):
        super(CodeNode, self).setData(column, value)
        if   column is 1: pass
        elif column is 2: self.value = value


class BaremeNode(Node):
    def __init__(self, code, description, value, parent, value_type = None):
        super(BaremeNode, self).__init__(code, description, parent)
        self.value = value
        # create a copy of the default value by hand
        self.default = TaxScale(value._name, option = value.option)
        for s , t in value._brackets:
            self.default.add_bracket(s, t)
        self.default.marginal_to_average()
        self.type_info = 'BAREME'
        self.value_type  = value_type

    def _recurseXml(self, parent, datesim):
        if self.isDirty():
            child = SubElement(parent,
                               tag = self.type_info,
                               attrib = {'code': self.code,
                                         'description': self.description})

            tax_scale = self.value
            S = tax_scale.seuils
            T = tax_scale.taux

            for i in range(self.value._nb):
                tranche = SubElement(child,
                                     tag = 'TRANCHE',
                                     attrib = {'code': 'tranche%d' % i})

                seuil = SubElement(tranche,
                                     tag = 'SEUIL',
                                     attrib = {'code': 'tranche%d' % i})

                SubElement(seuil,
                           tag = 'VALUE',
                           attrib = {'valeur': '%f' % S[i],
                                     'deb': datesim,
                                     'fin': datesim})

                taux = SubElement(tranche,
                                     tag = 'TAUX')

                SubElement(taux,
                           tag = 'VALUE',
                           attrib = {'valeur': '%f' % T[i],
                                     'deb': datesim,
                                     'fin': datesim})

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
        if self.value._brackets == self.default._brackets:
            return False
        return True
