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

from core.datatable import DataTable, SystemSf
from parametres.paramData import XmlReader, Tree2Object
from france.utils import Scenario
from france.model.data import InputTable
from france.model.model import ModelSF
from core.utils import gen_output_data, gen_aggregate_output, of_import
from datetime import datetime

import gc



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
        
    def set_config(self, **kwargs):
        '''
        Sets the directory where to find the openfisca source and adjust some directories
        '''
        
        for key, val in kwargs.iteritems():
            if key == "year":
                date_str = str(val)+ '-01-01'
                self.datesim = datetime.strptime(date_str ,"%Y-%m-%d").date() 
                        
            if hasattr(self, key):
                setattr(self, key, val)
                
        # set defaults if ...
        if self.country is None:
            self.country = 'france'
    
        if self.param_file is None:
            if self.country is not None:
                self.param_file = '../' + self.country + '/param/param.xml'

        if self.totaux_file is None:
            if self.country is not None:
                self.totaux_file = '../' + self.country + '/totaux.xml'
        


    def initialize(self):
        '''
        Initializes using config
        '''
        # sets required
        if self.country is not None:            
#                if self.InputTable is not None:
#                    del self.InputTable
            self.InputTable = of_import('model.data', 'InputTable')
    
#                if self.ModelSF is not None:
#                    del self.ModelSF
            self.ModelSF = of_import('model.model', 'ModelSF')        
    
#                if self.Scenario is not None:
#                    del self.Scenario
            Scenario = of_import('utils', 'Scenario')

        print self.param_file
        self.set_param()
                        
    def set_param(self):
        '''
        Sets the parameters of the simulation
        '''
        print self.datesim
        reader = XmlReader(self.param_file, self.datesim)
        rootNode = reader.tree
        
        self.P_default = Tree2Object(rootNode, defaut = True)
        self.P_default.datesim = self.datesim

        self.P = Tree2Object(rootNode, defaut = False)
        self.P.datesim = self.datesim
              
    def compute(self):
        NotImplementedError          
    
  
class ScenarioSimulation(Simulation):
    def __init__(self):
        super(ScenarioSimulation, self).__init__()
        
        self.scenario = None
        self.nmen = None

    
    def set_scenario(self, scenario = None):
        if scenario is None:
            self.scenario = Scenario()
        else:
            self.scenario = scenario  

    def compute(self):
        """
        Computes output_data from scenario
        """
        input_table = DataTable(InputTable, scenario = self.scenario)
        population_courant = SystemSf(ModelSF, self.P, self.P_default)
        population_courant.set_inputs(input_table)
        return gen_output_data(population_courant, self.totaux_fname)


class SurveySimulation(Simulation):
    def __init__(self):
        super(SurveySimulation, self).__init__()
        
        self.survey = None

  
    def set_survey(self, filename = None, datesim = None):
        '''
        Sets survey input data
        '''
        if datesim is None and self.datesim is not None:
            datesim = self.datesim
        if self.country is not None:
            filename = '../%s/data/survey.h5' %(self.country)
        self.survey = DataTable(self.InputTable, survey_data = filename, datesim = datesim)

    def compute(self):
        """
        Computes output_data from scenario
        """
        
        # Clear outputs
        self.survey_outputs = None
        self.survey_outputs_default = None
        gc.collect()

        self.survey_outputs, self.survey_outputs_default = self.calculate_all()
        
        # Compute aggregates
        data = gen_aggregate_output(self.survey_outputs)
        descr = [self.survey.description, self.survey_outputs.description]
        data_default = None
        if self.reforme:
            data_default = gen_aggregate_output(self.survey_outputs_default)

        return data, data_default

    def preproc(self, input_table):
        '''
        Prepare the output values according to the ModelSF definitions/Reform status/input_table
        '''
        P_default = self.P_default # _parametres.getParam(defaut = True)    
        P         = self.P         # _parametres.getParam(defaut = False)
        
        output = SystemSf(self.ModelSF, P, P_default)
        output.set_inputs(input_table)
                
        if self.reforme:
            output_default = SystemSf(self.ModelSF, P_default, P_default)
            output_default.set_inputs(input_table)
        else:
            output_default = output
    
        return output, output_default


    def calculate_all(self):
        '''
        Computes all prestations
        '''
        input_table = self.survey
        output, output_default = self.preproc(input_table)
        
        output.calculate()
        if self.reforme:
            output_default.reset()
            output_default.calculate()
        else:
            output_default = output
    
        return output, output_default


class SimulationResults(object):
    """
    A SimulationResults object should contains all attributes to deal with 
    the results of a
    compute a simulation from a scenario or a survey
    It should also provide results that can be used by other functions
    """
    pass



    
    
    