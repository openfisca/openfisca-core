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
from core.datatable import DataTable, Column

class Prestation(Column):
    '''
    Prestation is a wraper around a function which takes some arguments and return a single array. 
    _P is a reserved kwargs intended to pass a tree of parametres to the function
    '''
    count = 0
    def __init__(self, func, unit= 'ind', label = None):
        super(Prestation, self).__init__(label, default = 0)

        self._order = Prestation.count
        Prestation.count += 1
        
        # initialize attribute
        self._isCalculated = False
        self._option = {}
        self._func = func
        self._unit  = unit
        self.inputs = set(func.__code__.co_varnames[:func.__code__.co_argcount])
        self._children  = set() # prestations immidiately affected by curtent prestation 
        self._parents = set() # prestations that current prestations depends on  
        self.descendants = set()
        self.ascendants  = set()

        # check if the function func needs parameter tree _P
        self._needParam = '_P' in self.inputs
        if self._needParam:
            self.inputs.remove('_P')
            
        # check if an option dict is passed to the function
        self._hasOption = '_option' in self.inputs
        if self._hasOption:
            self.inputs.remove('_option')
            self._option = func.func_defaults[0]
            for var in self._option:
                if var not in self.inputs:
                    raise Exception('%s in option but not in function args' % var)

    def set_param(self, P):
        if self._needParam:
            self._P = P
        else:
            raise Exception('trying to set param to a Prestation that does not need param')
    
    def addChild(self, prestation):
        self._children.add(prestation)
        prestation._parents.add(self)

    def calculate(self, inputs, index):
        '''
        Solver: finds dependencies and calculate accordingly all needed variables 
        '''
        print self._name
        if self._isCalculated:
            return

        idx = index[self._unit]

        required = set(self.inputs)
        funcArgs = {}
        for var in required:
            if var in inputs.col_names:
                if var in self._option: 
                    funcArgs[var] = getattr(inputs, var).get_value(idx, self._option[var])
                else:
                    funcArgs[var] = getattr(inputs, var).get_value(idx)
        
        for var in self._parents:
            varname = var._name
            if varname in funcArgs:
                raise Exception('%s provided twice: %s was found in primitives and in parents' %  (varname, varname))
            var.calculate(inputs, index)
            if varname in self._option: 
                funcArgs[varname] = var.get_value(idx, self._option[varname])
            else:
                funcArgs[varname] = var.get_value(idx)
        
        if self._needParam:
            funcArgs['_P'] = self._P
            required.add('_P')
        
        provided = set(funcArgs.keys())        
        if provided != required:
            raise Exception('%s missing: %s needs %s but only %s were provided' % (str(list(required - provided)), self._name, str(list(required)), str(list(provided))))
        self.set_value(self._func(**funcArgs), idx)
        self._isCalculated = True

    def dep_resolve(self, resolved=set(), unresolved=set()):
        '''
        Dependency solver.
        Algorithm found here http://www.electricmonk.nl/log/2008/08/07/dependency-resolving-algorithm/
        '''
        edges = self._parents
        unresolved.add(self)
        for edge in edges:
            if edge not in resolved:
                if edge in unresolved:
                    raise Exception('Circular reference detected: %s -> %s' % (self._name, edge._name))
                edge.dep_resolve(resolved, unresolved)
        
        resolved.add(self)
        unresolved.remove(self)

class SystemSf(DataTable):
    def __init__(self, param, title=None, comment=None):
        DataTable.__init__(self, title, comment)
        self._primitives = set()
        self._param = param
        self._inputs = None
        self._index = None
        self.build()

    def get_primitives(self):
        """
        Return socio-fical system primitives, ie variable needed as inputs
        """
        return self._primitives

    def build(self):
        # Build the closest dependencies  
        for column in self._columns:
            if column._needParam: column.set_param(self._param)
            for requiredVarName in column.inputs:
                found = False
                for potentialPresta in self._columns:
                    if requiredVarName == potentialPresta._name: # TODO: Generalize to more outputs ?
                        potentialPresta.addChild(column)
                        found = True
                        break
                if not found:
                    self._primitives.add(requiredVarName)
        
    def set_inputs(self, inputs):
        '''
        sets the input DataTable
        '''
        if not isinstance(inputs, DataTable):
            raise TypeError('inputs must be a DataTable')
        # check if all primitives are provided by the inputs
        for prim in self._primitives:
            if not prim in inputs.col_names:
                raise Exception('%s is a required input and was not found in inputs' % prim)
        # store inputs and indexes and nrows
        self._inputs = inputs
        self._index = inputs.index
        self._nrows = inputs._nrows

        self._init_columns(self._nrows)
        
    def calculate(self, var = None):
        if var is None:
            return "Will calculate all"
        if not self._primitives <= self._inputs.col_names:
            raise Exception('%s are not set, use set_inputs before calling calculate. Primitives needed: %s, Inputs: %s' % (self._primitives - self._inputs.col_names, self._primitives, self._inputs.col_names))
        column = getattr(self, var)
        column.calculate(self._inputs, self._index)
        
