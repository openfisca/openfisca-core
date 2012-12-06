# -*- coding:utf-8 -*-
"""
Created on Nov 30, 2012
@author: Mahd Ben Jelloul

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

from datetime import datetime
import gc
import os
from core.datatable import DataTable, SystemSf
from parametres.paramData import XmlReader, Tree2Object
from core.utils import gen_output_data, of_import
from src import SRC_PATH

from pandas import DataFrame

class Simulation(object):
    """
    A simulation objects should contains all attributes to compute a simulation from a scenario or a survey
    It should also provide results that can be used by other functions
    """
    
    def __init__(self):
        super(Simulation, self).__init__()

        self.reforme = False
        self.country = None
        self.datesim = None
        self.P = None
        self.P_default = None
        self.totaux_file = None
        self.param_file = None
        
    def _set_config(self, **kwargs):
        '''
        Sets some general Simulation attributes 
        '''
        
        remaining = kwargs.copy()
        
        for key, val in kwargs.iteritems():
            if key == "year":
                date_str = str(val)+ '-01-01'
                self.datesim = datetime.strptime(date_str ,"%Y-%m-%d").date()
                remaining.pop(key)
                
            elif key in ['country', 'param_file', 'totaux_file']:
                if hasattr(self, key):
                    setattr(self, key, val)
                    remaining.pop(key)
                    
        if self.country is None:
            self.country = 'france'
            if "country" in remaining:
                remaining.pop('country')
    
        if self.param_file is None:
            if self.country is not None:
                self.param_file = os.path.join(SRC_PATH, self.country, 'param', 'param.xml')
                
        if self.totaux_file is None:
            if self.country is not None:
                self.totaux_file = os.path.join(SRC_PATH, self.country, 'totaux.xml')
                
        # Sets required country specific classes
        if self.country is not None:            
            self.InputTable = of_import('model.data', 'InputTable', country = self.country)
            self.ModelSF = of_import('model.model', 'ModelSF', country = self.country)        

        # TODO: insert definition of fam foy , QUIMEN QUIFOY etc etc here !

        return remaining
                        
    def set_param(self, P = None, P_default = None):
        '''
        Sets the parameters of the simulation
        '''
        reader = XmlReader(self.param_file, self.datesim)
        rootNode = reader.tree

        if P_default is None:
            self.P_default = Tree2Object(rootNode, defaut = True)
            self.P_default.datesim = self.datesim
        else:
            self.P_default = P_default
            
        if P is None:
            self.P = Tree2Object(rootNode, defaut = False)
            self.P.datesim = self.datesim
        else:
            self.P = P
              
    def compute(self):
        NotImplementedError          
        
    def _preproc(self, input_table):
        '''
        Prepare the output values according to the ModelSF definitions/Reform status/input_table
        '''
        P_default = self.P_default     
        P         = self.P                 
        output = SystemSf(self.ModelSF, P, P_default)
        output.set_inputs(input_table, country = self.country)
                
        if self.reforme:
            output_default = SystemSf(self.ModelSF, P_default, P_default)
            output_default.set_inputs(input_table, country = self.country)
        else:
            output_default = output
    
        return output, output_default


    def clear(self):
        NotImplementedError
  
class ScenarioSimulation(Simulation):
    '''
    A Simulation class tailored to deal with scenarios
    '''
    def __init__(self):
        super(ScenarioSimulation, self).__init__()
        
        self.scenario = None
        self.nmen = None
        self.xaxis = None
        self.maxrev = None
        self.mode = None
       
    def set_config(self, **kwargs):
        '''
        Configures the ScenarioSimulation
        '''
        specific_kwargs = self._set_config(**kwargs)
        self.Scenario = of_import('utils', 'Scenario', country = self.country)
        if self.scenario is None:
            try:                
                self.scenario = kwargs['scenario']
            except:
                self.scenario = self.Scenario()

        self.scenario.year = self.datesim.year
        for key, val in specific_kwargs.iteritems():        
                if hasattr(self, key):
                    setattr(self, key, val)
        
        self.scenario.nmen   = self.nmen
        self.scenario.maxrev = self.maxrev
        self.scenario.xaxis  = self.xaxis

    def compute(self):
        """
        Computes output_data from scenario
        """
        
        input_table = DataTable(self.InputTable, scenario = self.scenario)
        output, output_default = self._preproc(input_table)
        data = gen_output_data(output)
        
        if self.reforme:
            output_default.reset()
            data_default = gen_output_data(output_default) # TODO: take gen_output_data form core.utils
            data.difference(data_default)
        else:
            data_default = data

        return data, data_default


class SurveySimulation(Simulation):
    '''
    A Simaultion class tailored to deal with survey data
    '''
    def __init__(self):
        super(SurveySimulation, self).__init__()
        
        self.survey = None
        self.descr = None
        self.outputs = None
        self.outputs_default = None
  
        self.label2var = dict()
        self.var2label = dict()
        self.var2enum  = dict() 

    
    def set_config(self, **kwargs):
        '''
        Configures the SurveySimulation
        '''
        # Setting general attributes and getting the specific ones
        specific_kwargs = self._set_config(**kwargs)

        for key, val in specific_kwargs.iteritems():        
                if hasattr(self, key):
                    setattr(self, key, val)
  
    def set_survey(self, filename = None, datesim = None):
        '''
        Sets survey input data
        '''
        if datesim is None and self.datesim is not None:
            datesim = self.datesim
            
        if filename is None:
            if self.country is not None:
                filename = os.path.join(SRC_PATH, self.country, 'data', 'survey.h5')
            
        self.survey = DataTable(self.InputTable, survey_data = filename, datesim = datesim)
        self._build_dicts(option = 'input_only')

    def compute(self):
        """
        Computes output_data from scenario
        """            
        # Clear outputs
        self.clear()
        gc.collect()
        self.outputs, self.outputs_default = self._calculate_all()
        self._build_dicts(option = 'output_only')

    def aggregated_by_household(self, varlist = None, all_output_vars = True, all_input_vars = False):
        """
        Generates aggregates at the household level ('men')
        """
        print "Aggregating households"
        if self.outputs is None:
            raise Exception('outputs should be no None')
        
        models = [self.outputs]
        if self.reforme is True:
            models.append(self.outputs_default) 
        
        out_tables = []
        
        for model in models:
            out_dct = {}
            inputs = model._inputs
            unit = 'men'
            idx = model.index[unit]
            enum = inputs.description.get_col('qui'+unit).enum
            people = [x[1] for x in enum]

            input_varlist = set(['wprm'])
            if all_input_vars:           
                input_varlist = input_varlist.union(set(inputs.col_names))
            if varlist is not None:
                input_varlist = input_varlist.union( set(inputs.col_names).intersection(varlist))
 

            if varlist is not None:
                output_varlist = set(model.col_names).intersection(varlist)
            if all_output_vars:
                output_varlist = set(model.col_names)
                
            varnames = output_varlist.union(input_varlist)
            for varname in varnames:
                if varname in model.col_names:
                    if model.description.get_col(varname)._unit != unit:
                        val = model.get_value(varname, idx, opt = people, sum_ = True)    
                    else:
                        val = model.get_value(varname, idx)
                elif varname in inputs.col_names:
                    val = inputs.get_value(varname, idx)
                else:
                    raise Exception('%s was not find in model nor in inputs' % varname)
                
                out_dct[varname] = val      
            # TODO: should take care the variables that shouldn't be summed automatically
            
            out_tables.append(DataFrame(out_dct))
        
        if self.reforme is False:
                out_tables.append(None)
                
        return out_tables[0], out_tables[1]

    @property
    def input_var_list(self):
        '''
        List of survey variables
        '''
        return self.survey.description.col_names
        
    @property
    def output_var_list(self):
        '''
        List of survey variables
        '''
        return self.outputs.description.col_names
        
    @property
    def var_list(self):
        '''
        List of variables pesent in survey and output
        '''
        return list(set(self.survey.description.col_names).union(set(self.outputs.description.col_names)))
        

    def _build_dicts(self, option = None):
        '''
        Builds dictionaries from description
        '''
        try:
            if option is 'input_only':
                descriptions = [self.survey.description]
            elif option is 'output_only': 
                descriptions = [self.outputs.description]
            else:
                descriptions = [self.survey.description, self.outputs.description] 
        except:
            descriptions = [self.survey.description]
        
        for description in descriptions:
            l2v, v2l, v2e = description.builds_dicts()
            self.label2var.update(l2v)
            self.var2label.update(v2l)
            self.var2enum.update(v2e)

    def _calculate_all(self):
        '''
        Computes all prestations
        '''
        input_table = self.survey
        output, output_default = self._preproc(input_table)
        
        output.calculate()
        if self.reforme:
            output_default.reset()
            output_default.calculate()
        else:
            output_default = output

        return output, output_default

    def clear(self):
        '''
        Clears outputs table 
        '''
        self.survey_outputs = None
        self.survey_outputs_default = None
        
