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
from pandas import DataFrame, read_csv, HDFStore
from src.core.utils_old import of_import
from src.core.description import ModelDescription, Description



class DataTable(object):
    """
    Construct a SystemSf object is a set of Prestation objects
        * title [string]
        * comment [string]: text shown on the top of the first data item
    """
    def __init__(self, model_description, survey_data = None, scenario = None, datesim = None, country = None):
        super(DataTable, self).__init__()

        # Init instance attribute
        self.description = None
        self.scenario = None
        self._isPopulated = False
        self.col_names = []
        self.table = DataFrame()
        self.index = {}
        self._nrows = 0
        
        if datesim is None:
            raise Exception('InputTable: datesim should be provided')
        else:
            self.datesim = datesim 
            
        if country is None:
            raise Exception('InputTable: country should be provided')
        else:
            self.country = country
        
            
        self.survey_year = None
        
        # Build the description attribute        
        if type(model_description) == type(ModelDescription):
            descr = model_description()
            self.description = Description(descr.columns)
        else:
            raise Exception("model_description should be an ModelDescription inherited class")

        self.col_names = self.description.col_names

        if (survey_data is not None) and (scenario is not None):
            raise Exception("should provide either survey_data or scenario but not both")
        elif survey_data is not None:
            self.populate_from_survey_data(survey_data)
        elif scenario is not None:
            self.scenario = scenario
            scenario.populate_datatable(self)
        
    def gen_index(self, units):
        '''
        Genrates indexex for the relevant units
        '''
        
        self.index = {'ind': {0: {'idxIndi':np.arange(self._nrows), 
                                  'idxUnit':np.arange(self._nrows)},
                      'nb': self._nrows},
                      'noi': {}}
        dct = self.index['noi']
        nois = self.table.noi.values
        listnoi = np.unique(nois)
        for noi in listnoi:
            idxIndi = np.sort(np.squeeze((np.argwhere(nois == noi))))
            idxUnit = np.searchsorted(listnoi, nois[idxIndi])
            temp = {'idxIndi':idxIndi, 'idxUnit':idxUnit}
            dct.update({noi: temp}) 

        for unit in units:
            enum = self.description.get_col('qui'+unit).enum
            try:
                idx = getattr(self.table, 'id'+unit).values
                qui = getattr(self.table, 'qui'+unit).values
                enum = self.description.get_col('qui'+unit).enum
            except:
                raise Exception('DataTable needs columns %s and %s to build index with unit %s' %
                          ('id' + unit, 'qui' + unit, unit))

            self.index[unit] = {}
            dct = self.index[unit]
            idxlist = np.unique(idx)
            dct['nb'] = len(idxlist)

            for full, person in enum:
                idxIndi = np.sort(np.squeeze((np.argwhere(qui == person))))
#                if (person == 0) and (dct['nb'] != len(idxIndi)):
#                    raise Exception('Invalid index for %s: There is %i %s and %i %s' %(unit, dct['nb'], unit, len(idxIndi), full))
                idxUnit = np.searchsorted(idxlist, idx[idxIndi])
                temp = {'idxIndi':idxIndi, 'idxUnit':idxUnit}
                dct.update({person: temp}) 
    
    def propagate_to_members(self, unit , col):
        '''
        Set the variable of all unit member to the value of the (head of) unit
        '''
        index = self.index[unit]
        value = self.get_value(col, index)
        try:
            enum = self.description.get_col('qui'+unit).enum
        except:
            enum = self._inputs.description.get_col('qui'+unit).enum
        
        for member in enum:
            self.set_value(col, value, index, opt = member[1])


    def populate_from_survey_data(self, fname, year = None):
        '''
        Populates a DataTable from survey data
        '''

        if self.country is None:
            raise Exception('DataTable: country key word variable must be set') 
               
        INDEX = of_import(None, 'ENTITIES_INDEX', self.country)
        
        if fname[-4:] == '.csv':
            with open(fname) as survey_data_file:
                self.table = read_csv(survey_data_file)

        elif fname[-3:] == '.h5':
            store = HDFStore(fname)
            available_years = sorted([int(x[-4:]) for x in  store.keys()])
            
            if year is None:
                if self.datesim is not None:
                    year_ds  = self.datesim.year
                else:
                    raise Exception('self.datesim or year should be defined') 
            else:
                year_ds = year
           
            yr = year_ds+0 # to avoid pointers problem
            while yr not in available_years and yr > available_years[0]:
                yr = yr - 1
            base_name = 'survey_'+ str(yr)
            if year_ds != yr:
                print 'Survey data for year %s not found. Using year %s' %(str(year_ds), str(yr))
            else:
                print 'Survey data for year %s found' %str(year_ds)

            if yr in available_years:
                self.survey_year = yr
            self.table = store[str(base_name)] 
            store.close()
            
        self._nrows = self.table.shape[0]
        missing_col = []
        for col in self.description.columns.itervalues():
            if not col.name in self.table:
                missing_col.append(col.name)
                self.table[col.name] = col._default
            try:   
                self.table[col.name] = self.table[col.name].astype(col._dtype)
            except:
                raise Exception("Impossible de lire la variable suivante issue des données d'enquête :\n %s \n  " %col.name)
            
        if missing_col:
            message = "%i input variables missing\n" % len(missing_col)
            for var in missing_col:
                message += '  - '+ var + '\n'
            print Warning(message)
        
        for var in INDEX:
            if ('id' + var) in missing_col:
                raise Exception('Survey data needs variable %s' % ('id' + var))
            
            if ('qui' + var) in missing_col:
                raise Exception('Survey data needs variable %s' % ('qui' + var))

        
        self.gen_index(INDEX)
        self._isPopulated = True
        
        self.set_value('wprm_init', self.get_value('wprm'),self.index['ind'])
        

    def get_value(self, varname, index = None, opt = None, sum_ = False):
        '''
        method to read the value in an array
        index is a dict with the coordinates of each person in the array
            - if index is none, returns the whole column (every person)
            - if index is not none, return an array of length len(unit)
        opt is a dict with the id of the person for which you want the value
            - if opt is None, returns the value for the person 0 (i.e. 'vous' for 'foy', 'chef' for 'fam', 'pref' for 'men')
            - if opt is not None, return a dict with key 'person' and values for this person
        '''
        col = self.description.get_col(varname)
        dflt = col._default
        dtyp = col._dtype
        var = np.array(self.table[varname].values, dtype = col._dtype)
        if index is None:
            return var
        nb = index['nb']
        if opt is None:
            temp = np.ones(nb, dtype = dtyp)*dflt
            idx = index[0]
            temp[idx['idxUnit']] = var[idx['idxIndi']]
            return temp
        else:
            out = {}
            for person in opt:
                temp = np.ones(nb, dtype = dtyp)*dflt
                idx = index[person]
                temp[idx['idxUnit']] = var[idx['idxIndi']]
                out[person] = temp
            if sum_ is False:
                return out
            else:
                sumout = 0
                for val in out.itervalues():
                    sumout += val
                return sumout

    def set_value(self, varname, value, index, opt = None):
        '''
        Sets the value of varname using index and opt
        '''
        if opt is None:
            idx = index[0]
        else:
            idx = index[opt]

        # this command should work on later pandas version...
        # self.table.ix[idx['idxIndi'], [varname]] = value

        # for now, we're doing it manually
        col = self.description.get_col(varname)
        values = self.table[varname].values
        
        dtyp = col._dtype
        temp = np.array(value, dtype = dtyp)
        var = np.array(values, dtype = dtyp)
        var[idx['idxIndi']] =  temp[idx['idxUnit']]
        self.table[varname] = var

    def to_csv(self, fname):
        self.table.to_csv(fname)
                  
    def __str__(self):
        return self.table.__str__()

    def inflate(self, varname, inflator):
        self.table[varname] = inflator*self.table[varname]


class SystemSf(DataTable):
    def __init__(self, model_description, param, defaultParam = None, datesim = None, country = None):
        DataTable.__init__(self, model_description, datesim = datesim, country = country)
        self._primitives = set()
        self._param = param
        self._default_param = defaultParam
        self._inputs = None
        self.index = None
        if datesim is not None:
            self.datesim = datesim
            
        self.reset()
        self.build()

    def get_primitives(self):
        """
        Return socio-fiscal system primitives, ie variable needed as inputs
        """
        return self._primitives

    def reset(self):
        """ sets all columns as not calculated """
        for col in self.description.columns.itervalues():
            col._isCalculated = False
    
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
        
    def set_inputs(self, inputs, country = None):
        ''' sets the input DataTable '''
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

        # initialize the pandas DataFrame to store data
        dct = {}
        for col in self.description.columns.itervalues():
            dflt = col._default
            dtyp = col._dtype
            dct[col.name] = np.ones(self._nrows, dtyp)*dflt
        
        self.table = DataFrame(dct)
        
        if country is None:
            country = 'france'
        preproc_inputs = of_import('utils','preproc_inputs', country = country)
        if preproc_inputs is not None:
            preproc_inputs(self._inputs)
        

    def calculate(self, varname = None):
        '''
        Solver: finds dependencies and calculate accordingly all needed variables 
        '''
        if varname is None:
            for col in self.description.columns.itervalues():
                try:
                    self.calculate(col.name)
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
        
        idx = self.index[col._unit]

        required = set(col.inputs)
        funcArgs = {}
        for var in required:
            if var in self._inputs.col_names:
                if var in col._option: 
                    funcArgs[var] = self._inputs.get_value(var, idx, col._option[var])
                else:
                    funcArgs[var] = self._inputs.get_value(var, idx)
        
        for var in col._parents:
            parentname = var.name
            if parentname in funcArgs:
                raise Exception('%s provided twice: %s was found in primitives and in parents' %  (varname, varname))
            self.calculate(parentname)
            if parentname in col._option:
                funcArgs[parentname] = self.get_value(parentname, idx, col._option[parentname])
            else:
                funcArgs[parentname] = self.get_value(parentname, idx)
        
        if col._needParam:
            funcArgs['_P'] = self._param
            required.add('_P')
            
        if col._needDefaultParam:
            funcArgs['_defaultP'] = self._default_param
            required.add('_defaultP')
        
        provided = set(funcArgs.keys())        
        if provided != required:
            raise Exception('%s missing: %s needs %s but only %s were provided' % (str(list(required - provided)), self._name, str(list(required)), str(list(provided))))
        self.set_value(varname, col._func(**funcArgs), idx)
        col._isCalculated = True