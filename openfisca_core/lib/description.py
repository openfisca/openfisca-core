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
from src.lib.columns import Column, Prestation

class MetaModelDescription(type):
    """
    DataTable metaclass
    
    Create class attribute `columns`: list of the ModelDescription class attributes,
    created in the same order as these attributes were written
    """
    def __new__(cls, name, bases, dct):

        Column.count = 0
        Prestation.count = 0
        columns = {}
        super_new = super(MetaModelDescription, cls).__new__
        parents = [b for b in bases if isinstance(b, MetaModelDescription)]
        if not parents:
            # If this isn't a subclass of ModelDescription, don't do anything special.
            return super_new(cls, name, bases, dct)
        

#        fake_column = Column()
#        fake_column.reset_count()
        for attrname, col in dct.items():
            if isinstance(col, Column):
                col.name = attrname
#                if attrname in columns:
#                    col._order = columns[attrname]._order
#                    raise Exception("column declared twice")
                columns[attrname] = col

        columns_list = columns.values()
        columns_list.sort(key=lambda x:x._order)
        col_numbers = set([x._order for x in columns_list])
        for i in range(max(col_numbers)):
            if not i in col_numbers:
                raise Exception("The column before %s in class %s is defined twice"% (columns_list[i].name, name))
        
        dct["columns"] = columns_list
        return super_new(cls, name, bases, dct)
        
class ModelDescription(object):
    __metaclass__ = MetaModelDescription

    def __init__(self):
        super(ModelDescription, self).__init__()

        comp_title, comp_comment = self._compute_title_and_comment()
        self.__title = comp_title
        self.__comment = comp_comment

    def _compute_title_and_comment(self):
        """
        Private method to compute title and comment of the data set from the docstring
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
        """ Return data set title """
        return self.__title
    
    def get_comment(self):
        """ Return data set comment """
        return self.__comment

    def to_string(self, debug=False, indent=None, align=False):
        """
        Return readable string representation of the data set
        
        Parameters
        ----------
        
        debug : bool, default False
                If true, show more details
        
        indent :  default None
        
        align : bool, default False 

        Returns
        -------
        txt : str
              Representation of the data set

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
            for column in self.columns:
                column_length = len(_get_label(column))
                if column_length > length:
                    length = column_length
        for column in self.columns:
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
    
    def __str__(self):
        return self.to_string(debug=True)



class Description(object):
    def __init__(self, columns):
        super(Description, self).__init__()
        self.columns = {}
        self._col_names = set()
        for col in columns:
            self.columns[col.name] = col
            self._col_names.add(col.name)
            
            
    @property
    def col_names(self):
        return self._col_names

    def get_col(self, col_name):
        return self.columns[col_name]

    def has_col(self, col_name):
        return self.columns.has_key(col_name)
    
    
    def builds_dicts(self):
        '''
        Builds dicts label2var, var2label, var2enum
        '''
        label2var = {}
        var2label = {}
        var2enum = {}
        from src.lib.columns import EnumCol
        for var in self.col_names:
            varcol  = self.get_col(var)
            if isinstance(varcol, EnumCol):
                var2enum[var] = varcol.enum
            else:
                var2enum[var] = None
                    
            if varcol.label:
                    label2var[varcol.label] = var
                    var2label[var]          = varcol.label        
            else:
                    label2var[var] = var
                    var2label[var] = var
        var2label['wprm'] = 'Effectif'
        label2var['Effectif'] = 'wprm'
        return label2var, var2label, var2enum