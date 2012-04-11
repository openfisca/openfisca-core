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
from Config import CONF
from datetime import datetime
from pandas import read_csv, DataFrame, concat
from core.calmar import calmar

from description import ModelDescription, Description
import pickle

class DataTable(object):
    """
    Construct a SystemSf object is a set of Prestation objects
        * title [string]
        * comment [string]: text shown on the top of the first data item
    """
    def __init__(self, model_description, external_data = None, scenario = None):
        super(DataTable, self).__init__()

        # Init instance attribute
        self.description = None
        self.scenario = None
        self._isPopulated = False
        self.col_names = []
        self.table = DataFrame()
        self.index = {}
        self._nrows = 0

        self.datesim = datetime.strptime(CONF.get('simulation', 'datesim') ,"%Y-%m-%d").date()

        self.NMEN = CONF.get('simulation', 'nmen')
        self.MAXREV = CONF.get('simulation', 'maxrev')
        self.XAXIS = CONF.get('simulation', 'xaxis') + 'i'
        
        # Build the description attribute        
        if type(model_description) == type(ModelDescription):
            descr = model_description()
            self.description = Description(descr.columns)
        else:
            raise Exception("model_description should be an ModelDescription inherited class")

        self.col_names = self.description.col_names

        if (external_data and scenario):
            raise Exception("should provide either external_data or scenario but not both")
        elif external_data:
            self.populate_from_external_data(external_data)
        elif scenario:
            self.populate_from_scenario(scenario)
        
    def gen_index(self, units):
#        idents = ['quimen', 'idmen']
#
#        self.table.set_index(idents, drop = False, inplace = True)

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
    
    def propagate_to_members(self, unit = 'men', col = "wprm"):
        '''
        Set the variable of all unit member to the value of the (head of) unit
        '''
        index = self.index[unit]
        value = self.get_value(col, index)
        enum = self.description.get_col('qui'+unit).enum
        for member in enum:
            self.set_value(col, value, index, opt = member[1])


    def inflate(self, totals):
        for varname in totals:
            if varname in self.table:
                x = sum(self.table[varname]*self.table['wprm'])/totals[varname]
                if x>0:
                    self.table[varname] = self.table[varname]/x

    def populate_from_external_data(self, fname):
        f = open(fname)
        self.table = read_csv(f)
        f.close()
        self._nrows = self.table.shape[0]
        missing_col = []
        for col in self.description.columns:
            name = col.name
            if not name in self.table:
                missing_col.append(name)
                self.table[name] = col._default
            self.table[name].astype(col._dtype)
        if missing_col:
            import warnings
            warnings.warn('%s missing' %  missing_col)
        
        self._isPopulated = True
        self.gen_index(['men', 'fam', 'foy'])
        self.set_zone_apl()
        
        self.set_value('wprm_init', self.get_value('wprm'),self.index['ind'])
#        self.calage()
        
    def set_zone_apl(self):
        data_dir = CONF.get('paths', 'data_dir')
        year = CONF.get('simulation','datesim')[:4]
        import os
        fname = os.path.join(data_dir, 'zone_apl_imputation_data')
        data_file = open(fname, 'rb')
        zone = pickle.load(data_file)
        data_file.close()
        code_vec = self.get_value('tu99') + 1e1*self.get_value('tau99') + 1e3*self.get_value('reg') + 1e5*self.get_value('pol99')        
        zone_apl = self.get_value('zone_apl')
        
        for code in zone.keys():
            if isinstance(zone[code], int):
                zone_apl[code_vec == code] = zone[code]
            else:
                np.random.seed(0)
                prob = np.random.rand(len(zone_apl[code_vec == code]))
                zone_apl[code_vec == code] = 1+ (zone[code][1]>prob) + (zone[code][2]> prob ) 
        self.set_value('zone_apl',zone_apl,self.index['men'])
        print self.get_value('zone_apl')    

    def calage(self):
        data_dir = CONF.get('paths', 'data_dir')
        year = CONF.get('simulation','datesim')[:4]
        import os
        if int(year) <= 2008:
            print 'calage'
            # update weights with calmar (demography)
            fname_men = os.path.join(data_dir, 'calage_men.csv')
            f_tot = open(fname_men)
            totals = read_csv(f_tot,index_col = (0,1))

            marges = {}
            for var, mod in totals.index:
                if not marges.has_key(var):
                    marges[var] = {}
                
                marges[var][mod] =  totals.get_value((var,mod),year)
            f_tot.close()
            
            print marges
            totalpop = marges.pop('totalpop')[0]
#            marges.pop('cstotpragr')
#            marges.pop('naf16pr')
#            marges.pop('typmen15')
#            marges.pop('ddipl')
#            marges.pop('ageq')
            marges.pop('act5') # variable la plus problématique
            param ={'use_proportions': True, 
                    'method': 'logit', 'lo':.1, 'up': 10,
                    'totalpop' : totalpop,
                    'xtol': 1e-6}
            self.update_weights(marges, param)
        
        #param  = {'totalpop': 62000000, 'use_proportions': True}

        # inflate revenues on totals
        fname = os.path.join(data_dir, 'calage.csv')
        f_tot = open(fname)
        totals = read_csv(f_tot,index_col = 0)
        totals = totals[year]
        f_tot.close()

        self.inflate(totals)             

    def populate_from_scenario(self, scenario):
        self._nrows = self.NMEN*len(scenario.indiv)
        MAXREV = self.MAXREV
        datesim = self.datesim

        self.table = DataFrame()

        idmen = np.arange(60001, 60001 + self.NMEN)
        for noi, dct in scenario.indiv.iteritems():
            birth = dct['birth']
            age = datesim.year- birth.year
            agem = 12*(datesim.year- birth.year) + datesim.month - birth.month
            noipref = dct['noipref']
            noidec = dct['noidec']
            noichef = dct['noichef']
            quifoy = self.description.get_col('quifoy').enum[dct['quifoy']]
            quifam = self.description.get_col('quifam').enum[dct['quifam']]
            quimen = self.description.get_col('quimen').enum[dct['quimen']]
            dct = {'noi': noi*np.ones(self.NMEN),
                   'age': age*np.ones(self.NMEN),
                   'agem': agem*np.ones(self.NMEN),
                   'quimen': quimen*np.ones(self.NMEN),
                   'quifoy': quifoy*np.ones(self.NMEN),
                   'quifam': quifam*np.ones(self.NMEN),
                   'idmen': idmen,
                   'idfoy': idmen*100 + noidec,
                   'idfam': idmen*100 + noichef}
            self.table = concat([self.table, DataFrame(dct)], ignore_index = True)

        self.gen_index(['foy', 'fam', 'men'])

        for name in self.col_names:
            if not name in self.table:
                self.table[name] = self.description.get_col(name)._default
            
        index = self.index['men']
        nb = index['nb']
        for noi, dct in scenario.indiv.iteritems():
            for var, val in dct.iteritems():
                if var in ('birth', 'noipref', 'noidec', 'noichef', 'quifoy', 'quimen', 'quifam'): continue
                if not index[noi] is None:
                    self.set_value(var, np.ones(nb)*val, index, noi)

        index = self.index['foy']
        nb = index['nb']
        for noi, dct in scenario.declar.iteritems():
            for var, val in dct.iteritems():
                if not index[noi] is None:
                    self.set_value(var, np.ones(nb)*val, index, noi)

        index = self.index['men']
        nb = index['nb']
        for noi, dct in scenario.menage.iteritems():
            for var, val in dct.iteritems():
                if not index[noi] is None:
                    self.set_value(var, np.ones(nb)*val, index, noi)
            
        # set xaxis
        # TODO: how to set xaxis vals properly
        if self.NMEN>1:
            var = self.XAXIS
            vls = np.linspace(0, MAXREV, self.NMEN)
            self.set_value(var, vls, {0:{'idxIndi': index[0]['idxIndi'], 'idxUnit': index[0]['idxIndi']}})
        
        self._isPopulated = True

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

class SystemSf(DataTable):
    def __init__(self, model_description, param, defaultParam = None):
        DataTable.__init__(self, model_description)
        self._primitives = set()
        self._param = param
        self._default_param = defaultParam
        self._inputs = None
        self.index = None
        self.reset()
        self.build()

    def get_primitives(self):
        """
        Return socio-fiscal system primitives, ie variable needed as inputs
        """
        return self._primitives

    def reset(self):
        """ sets all columns as not calculated """
        for col in self.description.columns:
            col._isCalculated = False
    
    def build(self):
        # Build the closest dependencies  
        for col in self.description.columns:
            # Disable column if necessary
            if col._start: 
                if col._start > self._param.datesim: col.set_disabled()
            if col._end:
                if col._end < self._param.datesim: col.set_disabled()
            
            for input_varname in col.inputs:
                if input_varname in self.description.col_names:
                    input_col = self.description.get_col(input_varname)
                    input_col.add_child(col)
                else:                    
                    self._primitives.add(input_varname)
        
    def set_inputs(self, inputs):
        ''' sets the input DataTable '''
        if not isinstance(inputs, DataTable):
            raise TypeError('inputs must be a DataTable')
        # check if all primitives are provided by the inputs
        for prim in self._primitives:
            if not prim in inputs.col_names:
                raise Exception('%s is a required input for %s and was not found in inputs' % prim)
        # store inputs and indexes and nrows
        self._inputs = inputs
        self.index = inputs.index
        self._nrows = inputs._nrows

        # initialize the pandas DataFrame to store data
        dct = {}
        for col in self.description.columns:
            dflt = col._default
            dtyp = col._dtype
            dct[col.name] = np.ones(self._nrows, dtyp)*dflt
        
        self.table = DataFrame(dct)
        
    def update_weights(self, marges, param = {}, weights_in='wprm_init', weights_out='wprm', return_margins = False):
        
        inputs = self._inputs
        data = {weights_in: inputs.get_value(weights_in, inputs.index['men'])}
        for var in marges:
            if var in inputs.col_names:
                data[var] = inputs.get_value(var, inputs.index['men'])
            else:
                if var != "totalpop":
                    data[var] = self.get_value(var, self.index['men'])
                
        val_pondfin, lambdasol, marge_new = calmar(data, marges, param = param, pondini=weights_in)

#        for var in marges.iterkeys():
#            print var
#            for mod in marges[var].iterkeys():
#                cat_varname = var + '_' + str(mod)
#                print 'target margin', marge_new[cat_varname], 'calib margin',  sum(val_pondfin*(data[var]==mod))
#    
        inputs.set_value(weights_out, val_pondfin, inputs.index['men'])
        inputs.propagate_to_members( unit='men', col = weights_out)
        
        # TODO propagate the changed weights for men to ind 
        if return_margins:
            return marge_new    
        
        
        
    def calculate(self, varname = None):
        '''
        Solver: finds dependencies and calculate accordingly all needed variables 
        '''
        if varname is None:
            # TODO:
            for col in self.description.columns:
                self.calculate(col.name)
            return "Will calculate all"

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


if __name__ == '__main__':
        import os
        fname_men = os.path.join('../data', 'calage_men.csv')
        #  fname_ind = os.path.join(data_dir, 'calage_ind.csv')
        
        
        f_tot = open(fname_men)
        totals = read_csv(f_tot,index_col = (0,1))
        
#        print totals
#        print totals.columns
#        print totals.index.names
        marges = {}
        for var, mod in totals.index:
            if not marges.has_key(var):
                marges[var] = {}
            marges[var][mod] =  totals.get_value((var,mod),'2006')
        f_tot.close()
        print marges