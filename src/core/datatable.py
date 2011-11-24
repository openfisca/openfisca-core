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
import numpy as np
from utils import Enum
QUIFAM = Enum(['chef', 'part', 'enf1','enf2','enf3','enf4','enf5','enf6','enf7','enf8','enf9'])

class Column(object):
    """
    DataSet data item
    
    `label` : (str, unicode)
    `default` : any type, optional
    """
    count = 0
    def __init__(self, label = None, default=None):
        self._order = Column.count
        Column.count += 1
        self._name = None
        self._nrows = None
        self._value = None
        self._label = label
        self._default = default
        self._dtype = None

    def set_name(self, name):
        self._name = name
        
    def get_name(self):
        return self._name

    def set_nrows(self, nrows):
        self._nrows = nrows

    def _init_value(self, nrows):
        self._nrows = nrows
        self._value = np.ones(nrows, dtype = self._dtype)*self._default

    def get_value(self, index = None, opt = None, dflt = 0):
        '''
        method to read the value in an array
        index is a dict with the coordinates of each person in the array
            - if index is none, returns the whole column (every person)
            - if index is not none, return an array of length len(unit)
        opt is a dict with the id of the person for which you want the value
            - if opt is None, returns the value for the person 0 (i.e. 'vous' for 'foy', 'chef' for 'fam', 'pref' for 'men')
            - if opt is not None, return a dict with key 'person' and values for this person
        '''
        var = self._value
        if index is None:
            return var
        nb = index['nb']
        if self._dtype == np.bool: dflt= (dflt != 0)
        if opt is None:
            temp = np.ones(nb, dtype = self._dtype)*dflt
            idx = index[0]
            temp[idx['idxUnit']] = var[idx['idxIndi']]
            return temp
        else:
            out = {}
            for person in opt:
                temp = np.ones(nb, dtype = self._dtype)*dflt
                idx = index[person]
                temp[idx['idxUnit']] = var[idx['idxIndi']]
                out[person] = temp
            return out

    def set_value(self, value, index, opt = None):
        if opt is None:
            idx = index[0]
        else:
            idx = index[opt]
        var = self._value
        val = np.array(value, dtype = self._dtype)
        var[idx['idxIndi']] = val[idx['idxUnit']]
        self._value = var

    def __str__(self):
        return '%s' % self._name

class DataTableMeta(type):
    """
    DataTable metaclass
    
    Create class attribute `_columns`: list of the DataTable class attributes,
    created in the same order as these attributes were written
    """
    def __new__(cls, name, bases, dct):
        columns = {}
        for base in bases:
            if getattr(base, "__metaclass__", None) is DataTableMeta:
                for column in base._columns:
                    columns[column._name] = column
                
        for attrname, value in dct.items():
            if isinstance( value, Column ):
                value.set_name(attrname)
                if attrname in columns:
                    value._order = columns[attrname]._order
                columns[attrname] = value
        columns_list = columns.values()
        columns_list.sort(key=lambda x:x._order)
        dct["_columns"] = columns_list
        return type.__new__(cls, name, bases, dct)

class DataTable(object):
    """
    Construct a SystemSf object is a set of Prestation objects
        * title [string]
        * comment [string]: text shown on the top of the first data item
    """
    __metaclass__ = DataTableMeta
    def __init__(self, nmen, title=None, comment=None):
        self._nmen = nmen
        self._nrows = nmen
        self.__title = title
        self.__comment = comment
        self.currentline = {}
        self.count = 0

        comp_title, comp_comment = self._compute_title_and_comment()
        if title is None:   self.__title = comp_title
        if comment is None: self.__comment = comp_comment
        
        self.col_names = set()
        self._isPopulated = False

    def _init_columns(self, nrows):
        for column in self._columns:
            self.col_names.add(column.get_name())
            column._init_value(nrows)
    
    def _compute_title_and_comment(self):
        """
        Private method to compute title and comment of the data set
        """
        comp_title = self.__class__.__name__
        comp_comment = None
        if self.__doc__:
            doc_lines = self.__doc__.splitlines()
            # Remove empty lines at the begining of comment
            while doc_lines and not doc_lines[0].strip():
                del doc_lines[0]
            if doc_lines:
                comp_title = doc_lines.pop(0).strip()
            if doc_lines:
                comp_comment = "\n".join([x.strip() for x in doc_lines])
        return comp_title, comp_comment

    def get_title(self):
        """
        Return data set title
        """
        return self.__title
    
    def get_comment(self):
        """
        Return data set comment
        """
        return self.__comment

    def gen_index(self, units):
        if not self._isPopulated:
            raise Exception('Table should be populated from a scenario or external data')
        
        self.index = {'ind': {0: {'idxIndi':np.arange(self._nrows), 
                                  'idxUnit':np.arange(self._nrows)},
                              'nb': self._nrows},
                      'noi': {}}
        dct = self.index['noi']
        nois = self.noi.get_value()
        listnoi = np.unique(nois)
        for noi in listnoi:
            idxIndi = np.sort(np.squeeze((np.argwhere(nois == noi))))
            idxUnit = np.searchsorted(listnoi, nois[idxIndi])
            temp = {'idxIndi':idxIndi, 'idxUnit':idxUnit}
            dct.update({noi: temp}) 
            
        for unit in units:
            try:
                idx = getattr(self, 'id'+unit).get_value()
                quicol = getattr(self, 'qui'+unit)
                qui = quicol.get_value()
                enum = quicol.enum
            except:
                raise Exception('DataTable needs columns %s and %s to build index with unit %s' %
                          ('id' + unit, 'qui' + unit, unit))

            self.index[unit] = {}
            dct = self.index[unit]
            idxlist = np.unique(idx)
            dct['nb'] = len(idxlist)
                        
            for person in enum.itervalues():
                idxIndi = np.sort(np.squeeze((np.argwhere(qui == person))))
                idxUnit = np.searchsorted(idxlist, idx[idxIndi])
                temp = {'idxIndi':idxIndi, 'idxUnit':idxUnit}
                dct.update({person: temp}) 

    def populate_from_scenario(self, scenario, date):
        self._nrows = self._nmen*len(scenario.indiv)
        self._init_columns(self._nrows)
        self.XAXIS = 'sal'
        self.MAXREV = 20000
        self.year = 2010
        self.datesim = date
        # pour l'instant, un seul menage répliqué n fois
        for noi, dct in scenario.indiv.iteritems():
            noipref = dct['noipref']
            noidec = dct['noidec']
            noichef = dct['noichef']
            quifoy = self.quifoy.enum[dct['quifoy']]
            quifam = self.quifam.enum[dct['quifam']]
            quimen = self.quimen.enum[dct['quimen']]
            self.addPerson(noi, quifoy, quifam, quimen, noidec, noichef, noipref)
        self._isPopulated = True

        self.gen_index(['foy', 'fam', 'men'])
                
        index = self.index['noi']
        for noi, dct in scenario.indiv.iteritems():
            for var, val in dct.iteritems():
                if var in ('birth', 'noipref', 'noidec', 'noichef', 'quifoy', 'quimen', 'quifam'): continue
                col = getattr(self, var)
                if not index[noi] is None:
                    col.set_value(np.ones(self._nmen)*val, index, noi)

    def addPerson(self, noi, quifoy, quifam, quimen, noidec, noichef, noipref):
        for i in xrange(self._nmen):
            indiv = self.row()
            indiv['noi']   = noi
            indiv['quifoy'] = quifoy
            indiv['quifam'] = quifam
            indiv['quimen'] = quimen
            indiv['idmen'] = 60000 + i + 1 
            indiv['idfoy'] = indiv['idmen']*100 + noidec
            indiv['idfam'] = indiv['idmen']*100 + noichef
            self.append()

    def append(self):
        if self.count >= self._nrows:
            raise Exception('La table est pleine')
        for key, val in self.currentline.iteritems():
            a = getattr(self, key).get_value()
            
            a[self.count] = val
        self.currentline = {}
        self.count += 1

    def row(self):
        return self.currentline

    def __str__(self):
        return self.to_string(debug=True)

    def to_string(self, debug=False, indent=None, align=False):
        """
        Return readable string representation of the data set
        If debug is True, add more details on data items
        """
        if indent is None:
            indent = "\n    "
        txt = self.__title+":"
        def _get_label(column):
            if debug:
                return column._name
            else:
                return column.get_prop_value("display", self, "label")
        length = 0
        if align:
            for column in self._columns:
                column_length = len(_get_label(column))
                if column_length > length:
                    length = column_length
        for column in self._columns:
            if debug:
                label = column._name
            else:
                label = column.get_prop_value("display", self, "label")
            if length:
                label = label.ljust(length)
                
            txt += indent+label+": "
            if debug:
                txt += column.__class__.__name__
        return txt
        
class IntCol(Column):
    '''
    A column of integer
    '''
    def __init__(self, label = None, default = 0):
        super(IntCol, self).__init__(label, default)
        self._dtype = np.int32
        
class EnumCol(IntCol):
    '''
    A column of integer
    '''
    def __init__(self, enum, label = None, default = 0):
        super(EnumCol, self).__init__(label, default)
        self.enum = enum
            
class BoolCol(Column):
    '''
    A column of boolean
    '''
    def __init__(self, label = None, default = False):
        super(BoolCol, self).__init__(label, default)
        self._dtype = np.bool
        
    def _init_value(self, nrows):
        self._nrows = nrows
        self._value = np.zeros(nrows, dtype = np.bool) | self._default
        
class FloatCol(Column):
    '''
    A column of float 32
    '''
    def __init__(self, label = None, default = 0):
        super(FloatCol, self).__init__(label, default)
        self._dtype = np.float32
        
class AgesCol(IntCol):
    '''
    A column of Int to store ages of people
    '''
    def __init__(self, label = None, default = 0):
        super(AgesCol, self).__init__(label, default)
        
    def get_value(self, index = None, opt = None, dflt = 0):
        return super(AgesCol, self).get_value(index, opt, dflt = -9999)

class DateCol(Column):
    '''
    A column of Int to store ages of people
    '''
    def __init__(self, label = None, default = 0):
        super(DateCol, self).__init__(label, default)
        self._dtype = np.datetime64

    def _init_value(self, nrows):
        self._nrows = nrows
        self._value = np.ones(nrows, dtype = self._dtype)
