# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
# https://github.com/openfisca/openfisca
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


import collections
from xml.dom import minidom

import numpy as np
from pandas import DataFrame

from . import model
from .datatables import DataTable


__all__ = ['TaxBenefitSystem']


preproc_inputs = None  # Set to a function by some country-specific extensions like OpenFisca-France


class OutNode(object):
    _vals = None
    children = None
    code = None
    color = None
    desc = None
    parent = None
    shortname = None
    typevar = None
    visible = 0

    def __init__(self, code, desc, shortname = '', vals = 0, color = (0, 0, 0), typevar = 0, parent = None):
        self.parent = parent
        self.children = []
        self.code = code
        self.desc = desc
        self.color = color
        self.typevar = typevar
        self._vals = vals
        self.shortname = shortname or code

    def __getitem__(self, key):
        if self.code == key:
            return self
        for child in self.children:
            val = child[key]
            if val is not None:
                return val

    def __iter__(self):
        for child in self.children:
            for descendant in child:
                yield descendant
        yield self

    def __repr__(self):
        return ''.join(self.iter_repr_fragments())

    def addChild(self, child):
        self.children.append(child)
        if child.color == (0,0,0):
            child.color = self.color
        child.setParent(self)

    def child(self, row):
        return(self.children[row])

    def childCount(self):
        return len(self.children)

    def difference(self, other):
        self.vals -= other.vals
        for child in self.children:
            child.difference(other[child.code])

    def hideAll(self):
        if self.code == 'revdisp':
            self.visible = 1
        else:
            self.visible = 0
        for child in self.children:
            child.hideAll()

    def iter_repr_fragments(self, tab_level = 0):
        yield '  ' * tab_level
        yield self.code
        yield ': '
        yield str(self.vals)
        yield '\n'
        child_tab_level = tab_level + 1
        for child in self.children:
            for fragment in child.iter_repr_fragments(child_tab_level):
                yield fragment

    def partiallychecked(self):
        return self.children and all(
            child.visible or child.partiallychecked()
            for child in self.children
            )

    def row(self):
        if self.parent is not None:
            return self.parent.children.index(self)

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

    def setLeavesVisible(self):
        for child in self.children:
            child.setLeavesVisible()
        if (self.children and (self.code !='revdisp')) or (self.code == 'nivvie'):
            self.visible = 0
        else:
            self.visible = 1

    def setParent(self, parent):
        self.parent = parent

    def setVisible(self, changeSelf = True, changeParent = True):
        if changeSelf:
            self.visible = 1
        if self.parent is not None:
            for sibling in self.parent.children:
                if not (sibling.partiallychecked() or sibling.visible ==1):
                    sibling.visible = 1
            if changeParent:
                self.parent.setVisible(changeSelf = False)

    def to_json(self):
        json = collections.OrderedDict((
            ('name', self.shortname),
            ('description', self.desc),
            ('type', self.typevar),
            ('values', self.vals.tolist()),
            ('color', [int(color_item) for color_item in self.color]),
            ))
        if self.children:
            json['children'] = collections.OrderedDict(
                (child.code, child.to_json())
                for child in self.children
                )
        return json

    def vals_get(self):
        return self._vals

    def vals_set(self, vals):
        dif = vals - self._vals
        self._vals = vals
        if self.parent:
            self.parent.vals = self.parent.vals + dif

    vals = property(vals_get, vals_set)


class TaxBenefitSystem(DataTable):
    def __init__(self, model_description, param, defaultParam = None, datesim = None, num_table = 1):
        super(TaxBenefitSystem, self).__init__(model_description, datesim = datesim, num_table = num_table)
        self._primitives = set()
        self._param = param
        self._default_param = defaultParam
        self._inputs = None
        self.index = None
        if datesim is not None:
            self.datesim = datesim

        self.reset()
        self.build()

    def __add__(self,other):
        """
        Addition of two TaxBenefitSystem.
        Add their output_table, iff it's the same simulation and only the survey differ
        """
        if not isinstance(other,TaxBenefitSystem):
            raise Exception("Can only add a TaxBenefitSystem to a SystemSF")

        assert self.num_table == other.num_table

        if self.num_table==1:
            self.table = self.table.append(other.table, verify_integrity=True)

        if self.num_table==3:
            assert(self.list_entities == other.list_entities)
            for ent in self.list_entities:
                self.table3[ent] = self.table3[ent].append(other.table3[ent])
        return self

    def build(self):
        # Build the closest dependencies
        for col in self.description.columns.itervalues():
            # Disable column if necessary
            col.set_enabled()
            if col._start:
                if col._start > self.datesim: col.set_disabled()
            if col._end:
                if col._end < self.datesim: col.set_disabled()

            for input_varname in col.inputs:
                if input_varname in self.description.col_names:
                    input_col = self.description.get_col(input_varname)
                    input_col.add_child(col)
                else:
                    self._primitives.add(input_varname)

    def calculate(self, varname = None):
        if (self.survey_data is not None) or (self.decomp_file is None) or (varname is not None):
            self.survey_calculate(varname=varname)
            return None
        elif self.test_case is not None:
            return self.test_case_calculate()
        else:
            raise Exception("survey_data or test_case attribute should not be None")

    def disable(self, disabled_prestations):
        """
        Sets some column as calculated so they are cot evaluated and keep their default value
        """
        if disabled_prestations is not None:
            for colname in disabled_prestations:
                self.description.columns[colname]._isCalculated = True

    def generate_output_tree(self, doc, output_tree, entity = 'men'):
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
                    output_tree.addChild(child)
                    self.generate_output_tree(element, child, entity)
        else:
            idx = entity
            inputs = self._inputs
            enum = inputs.description.get_col('qui'+entity).enum
            people = [x[1] for x in enum]
            if output_tree.code in self.col_names:
                self.calculate(varname=output_tree.code)
                val = self.get_value(output_tree.code, idx, opt = people, sum_ = True)
            elif output_tree.code in inputs.col_names:
                val = inputs.get_value(output_tree.code, idx, opt = people, sum_ = True)
            else:
                raise Exception('%s was not found in tax-benefit system nor in inputs' % output_tree.code)
            output_tree.vals = val

    def get_primitives(self):
        """
        Return socio-fiscal system primitives, ie variable needed as inputs
        """
        return self._primitives

    def reset(self):
        """
        Sets all columns as not calculated
        """
        for col in self.description.columns.itervalues():
            col._isCalculated = False

    def set_inputs(self, inputs):
        """
        Set the input DataTable

        Parameters
        ----------
        inputs : DataTable, required
                 The input variable datatable
        """
        if not isinstance(inputs, DataTable):
            raise TypeError('inputs must be a DataTable')
        # check if all primitives are provided by the inputs
#        for prim in self._primitives:
#            if not prim in inputs.col_names:
#                raise Exception('%s is a required input and was not found in inputs' % prim)

        # store inputs and indexes and nrows
        self._inputs = inputs
        self.index = inputs.index
        self._nrows = inputs._nrows

        self.survey_data = self._inputs.survey_data
        self.test_case = self._inputs.test_case
        # initialize the pandas DataFrame to store data

        if self.num_table == 1:
            dct = {}
            for col in self.description.columns.itervalues():
                dflt = col._default
                dtyp = col._dtype
                dct[col.name] = np.ones(self._nrows, dtyp)*dflt
            self.table = DataFrame(dct)

        if self.num_table == 3:
            self.table3 = {}
            temp_dct = {'ind' : {}, 'foy' : {}, 'men' : {}, 'fam' : {}}
            for col in self.description.columns.itervalues():
                dflt = col._default
                dtyp = col._dtype
                size = self.index[col.entity]['nb']
                temp_dct[col.entity][col.name] = np.ones(size, dtyp)*dflt
            for entity in self.list_entities:
                self.table3[entity] = DataFrame(temp_dct[entity])

        # Preprocess the input data according to country specification
        if preproc_inputs is not None:
            preproc_inputs(self._inputs)

    def survey_calculate(self, varname = None):
        '''
        Solver: finds dependencies and calculate accordingly all needed variables

        Parameters
        ----------

        varname : string, default None
                  By default calculate all otherwise, calculate only one variable

        '''
        WEIGHT = model.WEIGHT
        if varname is None:
            for col in self.description.columns.itervalues():
                try:
                    self.survey_calculate(varname = col.name)
                except Exception as e:
                    print e
                    print col.name
            return # Will calculate all and exit

        col = self.description.get_col(varname)

        if not self._primitives <= self._inputs.col_names:
            raise Exception('%s are not set, use set_inputs before calling calculate. Primitives needed: %s, Inputs: %s' % (self._primitives - self._inputs.col_names, self._primitives, self._inputs.col_names))

        if col._isCalculated:
            return

        if not col._enabled:
            return

        entity = col.entity
        if entity is None:
            entity = "ind"
        required = set(col.inputs)

        func_args = {}
        for var in required:
            if var in self._inputs.col_names:
                if var in col._option:
                    func_args[var] = self._inputs.get_value(var, entity, col._option[var])
                else:
                    func_args[var] = self._inputs.get_value(var, entity)

        for var in col._parents:
            parentname = var.name
            if parentname in func_args and parentname != WEIGHT :
                raise Exception('%s provided twice: %s was found in primitives and in parents' %  (varname, varname))
            self.survey_calculate(varname = parentname)
            opt, freq = None, None

            if parentname in col._option:
                opt = col._option[parentname]

            if parentname in col._freq:
                freq = col._freq[parentname]
                if freq[-1:] == "s": # to return dict with all months or trims
                    freqs = freq
                    func_args[parentname] = self.get_value(parentname, entity, opt=opt, freqs=freqs)
                else:
#                    print "coucou freq"
                    converter = var._frequency_converter(to_ = freq, from_= var.freq)
                    func_args[parentname] = converter(self.get_value(parentname, entity, opt=opt))
            else:
                func_args[parentname] = self.get_value(parentname, entity, opt=opt)

        if col._needParam:
            func_args['_P'] = self._param
            required.add('_P')

        if col._needDefaultParam:
            func_args['_defaultP'] = self._default_param
            required.add('_defaultP')

        provided = set(func_args.keys())
        assert provided == required, '%s missing: %s needs %s but only %s were provided' % (
            str(list(required - provided)), self._name, str(list(required)), str(list(provided)))

        try:
            self.set_value(varname, col._func(**func_args), entity)
        except:
            print varname
            raise

        col._isCalculated = True

    def test_case_calculate(self):
        assert self.decomp_file is not None, "A decomposition XML file should be provided as attribute decomp_file"

        decomp_doc = minidom.parse(self.decomp_file)
        output_tree = OutNode('root', 'root')
        self.generate_output_tree(decomp_doc, output_tree)
        return output_tree
