# -*- coding: utf-8 -*-
'''
Created on 16 nov. 2011

@author: Clem
'''
from __future__ import division
from core.datatable import DataTable, Column
import numpy as np

'''
the value of a prestation should be bound to a DataTable instance
'''

class Prestation(Column):
    '''
    Prestation is a wraper around a function which takes some arguments and return a single array. 
    _P is a reserved kwargs intended to pass a tree of parametres to the function
    '''
    count = 0
    def __init__(self, func, unit= 'ind', label = None, default = None, help = ''):
        super(Prestation, self).__init__(label, default, help)

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

    def set_param(self, P):
        if self._needParam:
            self._P = P
        else:
            raise Exception('trying to set param to a Prestation that does not need param')
    
    def set_value(self, value, index):
        nb = self._nrows
        idx = index[0]
        if self._value is None:
            var = np.zeros(nb)
        else:
            var = self._value
        var[idx['idxIndi']] = value[idx['idxUnit']]
        self._value = var

    def __str__(self):
        return '%s' % self._name

    def addChild(self, prestation):
        self._children.add(prestation)
        prestation._parents.add(self)

    def calculate(self, primitives, index):
        '''
        Calculation solver.
        '''
        if self._isCalculated:
            return

        idx = index[self._unit]

        required = set(self.inputs)
        funcArgs = {}
        for var in required:
            if var in [col._name for col in primitives._columns]:
                if var in self._option: 
                    funcArgs[var] = getattr(primitives, var).get_value(idx, self._option[var])
                else:
                    funcArgs[var] = getattr(primitives, var).get_value(idx)
        
        for var in self._parents:
            varname = var._name
            if varname in funcArgs:
                raise Exception('%s provided twice: %s was found in primitives and in parents' %  (varname, varname))
            var.calculate(primitives, index)
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

class SystemSfMeta(type):
    """
    SystemSf metaclass
    
    Create class attribute `_prestations`: list of the SystemSf class attributes,
    created in the same order as these attributes were written
    """
    def __new__(cls, name, bases, dct):
        prestations = {}
        for base in bases:
            if getattr(base, "__metaclass__", None) is SystemSfMeta:
                for prestation in base._prestations:
                    prestations[prestation._name] = prestation
                
        for attrname, value in dct.items():
            if isinstance( value, Prestation ):
                value.set_name(attrname)
                if attrname in prestations:
                    value._order = prestations[attrname]._order
                prestations[attrname] = value
        prestations_list = prestations.values()
        prestations_list.sort(key=lambda x:x._order)
        dct["_prestations"] = prestations_list
        return type.__new__(cls, name, bases, dct)



class SystemSf(object):
    """
    Construct a SystemSf object is a set of Prestation objects
        * title [string]
        * comment [string]: text shown on the top of the first data item
    """
    __metaclass__ = SystemSfMeta

    def __init__(self, param, title=None, comment=None):
        self.__title = title
        self.__comment = comment
        self._primitives = set()
        self._param = param
        self._inputs = None
        self._index = None
        self.__nrows = None
        comp_title, comp_comment = self._compute_title_and_comment()
        if title is None:   self.__title = comp_title
        if comment is None: self.__comment = comp_comment
        self.__changed = False
        self.build()

    def _init_columns(self, nrows):
        for prestation in self._prestations:
            prestation.set_nrows(nrows)
            
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
        Return socio-fical system title
        """
        return self.__title
    
    def get_comment(self):
        """
        Return socio-fical system comment
        """
        return self.__comment
    
    def get_primitives(self):
        """
        Return socio-fical system primitives, ie variable needed as inputs
        """
        return self._primitives

    def __str__(self):
        return self.to_string(debug=True)

    def buildPrestationsCloseDeps(self):
        # Build the closest dependencies  
        for prestation in self._prestations:
            if prestation._needParam: prestation.set_param(self._param)
            for requiredVarName in prestation.inputs:
                found = False
                for potentialPresta in self._prestations:
                    if requiredVarName == potentialPresta._name: # TODO: Generalize to more outputs ?
                        potentialPresta.addChild(prestation)
                        found = True
                        break
                if not found:
                    self._primitives.add(requiredVarName)
                    
    def build(self):
        self.buildPrestationsCloseDeps()
        
    def set_inputs(self, inputs):
        '''
        sets the input DataTable
        '''
        if not isinstance(inputs, DataTable):
            raise TypeError('inputs must be a DataTable')
        # check if all primitives are provided by the inputs
        for prim in self._primitives:
            if not prim in [col._name for col in inputs._columns]:
                raise Exception('%s is a required input and was not found in inputs' % prim)
        self._nrows = inputs._nrows
        self._init_columns(self._nrows)

        self._inputs = inputs
        self._index = inputs.index
        
    def calculate(self, var = None):
        if var is None:
            return "Will calculate all"
        if self._inputs is None:
            return Exception('inputs are not set, use set_inputs before calling calculate')
        prestation = getattr(self, var)
        prestation.calculate(self._inputs, self._index)
        
#    def check(self):
#        """
#        Check the dataset prestation values
#        """
#        errors = []
#        for prestation in self._prestations:
#            if not prestation.check_item(self):
#                errors.append(prestation._name)
#        return errors

    def to_string(self, debug=False, indent=None, align=False):
        """
        Return readable string representation of the data set
        If debug is True, add more details on data items
        """
        if indent is None:
            indent = "\n    "
        txt = self.__title+":"
        def _get_label(prestation):
            if debug:
                return prestation._name
            else:
                return prestation.get_prop_value("display", self, "label")
        length = 0
        if align:
            for prestation in self._prestations:
                prestation_length = len(_get_label(prestation))
                if prestation_length > length:
                    length = prestation_length
        for prestation in self._prestations:
            if debug:
                label = prestation._name
            else:
                label = prestation.get_prop_value("display", self, "label")
            if length:
                label = label.ljust(length)
                
            txt += indent+label+": "+"value_str"
            if debug:
                txt += " ("+prestation.__class__.__name__+")"
        return txt

#    @classmethod
#    def set_global_prop(klass, realm, **kwargs):
#        for prestation in klass._prestations:
#            prestation.set_prop(realm, **kwargs)

