# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


import datetime as dt
import gc
import os
from src.lib.datatable import DataTable, SystemSf
from src.parametres.paramData import XmlReader, Tree2Object
from src.lib.utils import gen_output_data, of_import
from src import SRC_PATH
from pandas import HDFStore

from pandas import DataFrame

from src.plugins.scenario.graph import drawTaux, drawBareme, drawBaremeCompareHouseholds, drawWaterfall


__all__ = ['Simulation', 'ScenarioSimulation', 'SurveySimulation' ]

class Simulation(object):
    """
    A simulation object contains all parameters to compute a simulation from a 
    test-case household (scenario) or a survey-like dataset 
    
    See also
    --------
    ScenarioSimulation, SurveySimulation 
    """
    def __init__(self):
        super(Simulation, self).__init__()
        self.reforme = False   # Boolean signaling reform mode 
        self.country = None    # String denoting the country 
        self.datesim = None        
        self.input_table = None   
        self.output_table, self.output_table_default = None, None
        self.P, self.P_default = None, None
        self.param_file = None
        self.disabled_prestations = None
        self.num_table = 1
        
        self.label2var = dict()
        self.var2label = dict()
        self.var2enum = dict()

        self.subset = None
        self.chunk = 1
        
        self.verbose = False  # verbosity parameter for debugging
                
    def _set_config(self, **kwargs):
        """
        Sets some general Simulation attributes 
        """
        remaining = kwargs.copy()
        
        for key, val in kwargs.iteritems():
            if key == "year":
                date_str = str(val)+ '-01-01'
                self.datesim = dt.datetime.strptime(date_str ,"%Y-%m-%d").date()
                remaining.pop(key)
                
            elif key == "datesim":
                if isinstance(val, dt.date):
                    self.datesim = val                    
                else:
                    self.datesim = dt.datetime.strptime(val ,"%Y-%m-%d").date()
                remaining.pop(key)
                
            elif key in ['country', 'param_file', 'decomp_file']:
                if hasattr(self, key):
                    setattr(self, key, val)
                    remaining.pop(key)
                    
        if self.country is None:
            self.country = 'france'
            if "country" in remaining:
                remaining.pop('country')
    
        if self.param_file is None:
            if self.country is not None:
                self.param_file = os.path.join(SRC_PATH, 'countries', self.country, 'param', 'param.xml')
                  
        # Sets required country specific classes
        if self.country is not None:
            try:
                del self.InputDescription
                del self.OutputDescription 
            except:
                pass
            self.InputDescription = of_import('model.data', 'InputDescription', country=self.country)
            self.OutputDescription = of_import('model.model', 'OutputDescription', country=self.country)        

        return remaining
                        
    def set_param(self, param=None, param_default=None):
        """
        Set the parameters of the simulation
        
        Parameters
        ----------
        param : a socio-fiscal parameter object to be used in the microsimulation. 
                By default, the method uses the one provided by the attribute param_file
        param_default : a socio-fiscal parameter object to be used 
                in the microsimulation to compute some gross quantities not available in the initial data. 
                parma_default is necessarily different from param when examining a reform
        """
        reader = XmlReader(self.param_file, self.datesim)
        rootNode = reader.tree

        if param_default is None:
            self.P_default = Tree2Object(rootNode, defaut=True)
            self.P_default.datesim = self.datesim
        else:
            self.P_default = param_default
            
        if param is None:
            self.P = Tree2Object(rootNode, defaut=False)
            self.P.datesim = self.datesim
        else:
            self.P = param

    
    def _initialize_input_table(self):
        self.input_table = DataTable(self.InputDescription, datesim=self.datesim, 
                                    country=self.country, num_table = self.num_table, 
                                    subset=self.subset,
                                    print_missing=self.verbose)


    def disable_prestations(self, disabled_prestations = None):
        """
        Disable some prestations that will remain to their default value
        
        Parameters
        ----------
        disabled_prestations : list of strings, default None
                               names of the prestations to be disabled
        """
        self.disabled_prestations = disabled_prestations

        
    def _preproc(self):
        """
        Prepare the output values according to the OutputDescription definitions/Reform status/input_table
        
        Parameters
        ----------
                
        input_table : DataTable

        Returns
        -------
        
        output, output_table_default : SystemSf
                                 DataTable of the output variable of the socio-fiscal model
        """
        P, P_default = self.P, self.P_default
        input_table = self.input_table
        
        output_table = SystemSf(self.OutputDescription, P, P_default, datesim = P.datesim, country = self.country, num_table = self.num_table)
        output_table.set_inputs(input_table, country = self.country)
                                
        if self.reforme:
            output_table_default = SystemSf(self.OutputDescription, P_default, P_default, datesim = P.datesim, country = self.country, num_table = self.num_table)
            output_table_default.set_inputs(input_table, country = self.country)
        else:
            output_table_default = output_table
    
        output_table.disable(self.disabled_prestations)
        output_table_default.disable(self.disabled_prestations)
        self._build_dicts()
        self.output_table, self.output_table_default = output_table, output_table_default
        

    def _compute(self, **kwargs):
        """
        Computes output_data for the Simulation
        
        Parameters
        ----------
        difference : boolean, default True
                     When in reform mode, compute the difference between actual and default  
        Returns
        -------
        data, data_default : Computed data and possibly data_default according to decomp_file
        
        """
        # Clear outputs
        #self.clear()

        self._preproc()
        output_table, output_table_default = self.output_table, self.output_table_default
        
        for key, val in kwargs.iteritems():
            setattr(output_table, key, val) 
            setattr(output_table_default, key, val) 
            
        data = output_table.calculate()
        if self.reforme:
            output_table_default.reset()
            output_table_default.disable(self.disabled_prestations)
            data_default = output_table_default.calculate()
        else:
            output_table_default = output_table
            data_default = data
        

        self.data, self.data_default = data, data_default
        self._build_dicts(option = 'output_only')
        gc.collect()


    def clear(self):
        """
        Clear the output_table 
        """
        self.output_table = None
        self.output_table_default = None
        gc.collect()
        

    def _build_dicts(self, option = None):
        """
        Builds dictionaries from description
        """
        try:
            if option is 'input_only':
                descriptions = [self.input_table.description]
            elif option is 'output_only': 
                descriptions = [self.output_table.description]
            else:
                descriptions = [self.input_table.description, self.output_table.description] 
        except:
            descriptions = [self.input_table.description]
        
        for description in descriptions:
            l2v, v2l, v2e = description.builds_dicts()
            self.label2var.update(l2v)
            self.var2label.update(v2l)
            self.var2enum.update(v2e)

    def get_col(self, varname, as_dataframe=False):
        '''
        Looks for a column in inputs description, then in output_table description
        '''
        if self.input_table.description.has_col(varname):
            return self.input_table.description.get_col(varname)
        
        if self.output_table is not None:
            if self.output_table.description.has_col(varname):
                return self.output_table.description.get_col(varname)
        else:
            print "Variable %s is absent from both inputs and output_table" % varname
            return None

    @property
    def input_var_list(self):
        """
        List of input survey variables
        
        Returns
        -------
        survey.description.col_names : List of input survey variables 
        """
        try:
            return self.input_table.description.col_names
        except:
            self._initialize_input_table()
            return self.input_table.description.col_names
        
    @property
    def output_var_list(self):
        """
        List of output survey variables
        """
        if self.output_table is not None:
            return self.output_table.description.col_names
        
        
    @property
    def var_list(self):
        """
        List the variables present in survey and output
        """
        if self.input_table is None:
            return
        try:
            return list(set(self.input_table.description.col_names).union(set(self.output_table.description.col_names)))
        except:
            return list(set(self.input_table.description.col_names))

    def create_description(self):
        '''
        Creates a description dataframe of the ScenarioSimulation
        '''
        now = dt.datetime.now()
        descr =  [u'OpenFisca', 
                         u'Calculé le %s à %s' % (now.strftime('%d-%m-%Y'), now.strftime('%H:%M')),
                         u'Système socio-fiscal au %s' % str(self.datesim)]
        # TODO: add other parameters
        return DataFrame(descr)


class ScenarioSimulation(Simulation):
    """
    A Simulation class tailored to deal with scenarios
    """
    
    def __init__(self):
        super(ScenarioSimulation, self).__init__()    
        self.Scenario = None
        self.scenario = None
        self.alternative_scenario = None
        self.decomp_file = None
        
        self.nmen = None
        self.xaxis = None
        self.maxrev = None
        self.mode = None
        self.same_rev_couple = False
        self.data = None
        self.data_default = None
       
    def set_config(self, **kwargs):
        """
        Configures the ScenarioSimulation
        
        Parameters
        ----------
        scenario : a scenario (by default, None selects Scenario())
        country  : a string containing the name of the country
        param_file : the socio-fiscal parameters file
        decomp_file : the decomp file
        xaxis : the revenue category along which revenue varies
        maxrev : the maximal value of the revenue
        same_rev_couple : divide the revenue equally between the two partners
        mode : 'bareme' or 'castype' TODO: change this 
        """
        
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
        self.scenario.same_rev_couple  = self.same_rev_couple
        
        if self.country is not None:              
            if self.decomp_file is None:
                default_decomp_file = of_import("decompositions", "DEFAULT_DECOMP_FILE", self.country)
                self.decomp_file = os.path.join(SRC_PATH, 'countries', self.country, 'decompositions', default_decomp_file)
            else:
                if not os.path.exists(self.decomp_file):
                    self.decomp_file = os.path.join(SRC_PATH, 'countries', self.country, 'decompositions', self.decomp_file)
        
        self.initialize_input_table()

    def get_varying_revenues(self, var):
        """
        List the potential varying revenues
        """
        build_axes = of_import('utils','build_axes', country = self.country)
        axes = build_axes(self.country)
        for axe in axes:
            if axe.col_name == var:
                rev = axe.typ_tot_default
                return rev
        raise Exception("No revenue for variable %s" %(var) )


    
    def reset_scenario(self):
        """
        Reset scenario and alternative_scenario to their default values 
        """
        if self.Scenario is not None:
            self.scenario = self.Scenario()
        self.alternative_scenario = None
        

    def set_alternative_scenario(self, scenario):
        """
        Set alternative-scenario
        
        Parameters
        ----------
        scenario : an instance of the class Scenario
        """
        self.alternative_scenario = scenario
        
    def set_marginal_alternative_scenario(self, entity = None, id_in_entity = None, variable = None, value = None):
        """
        Modifies scenario by changing the setting value of the variable of the individual with 
        position 'id' if necessary in entity named 'entity' 
        """
        self.alternative_scenario = self.scenario.copy()
        scenario = self.alternative_scenario
        if entity is not None:
            alt_entity = getattr(scenario, entity)
            if id_in_entity is not None:
                alt_entity[id_in_entity][variable] = value

    def initialize_input_table(self):
        """
        Initializee the input table of the ScenarioSimulation
        """        
        self._initialize_input_table()

    def compute(self, difference=False):
        """
        """
        self.input_table.load_data_from_test_case(self.scenario)
        self._preproc()
        
        alter = self.alternative_scenario is not None
        if self.reforme and alter:
            raise Exception("ScenarioSimulation: 'self.reforme' cannot be 'True' when 'self.alternative_scenario' is not 'None'") 

        if alter:
            input_table_alter = DataTable(self.InputDescription, datesim = self.datesim, country = self.country) 
            input_table_alter.load_data_from_test_case(self.alternative_scenario)
        
        if self.reforme and alter:
            raise Exception("ScenarioSimulation: 'self.reforme' cannot be 'True' when 'self.alternative_scenario' is not 'None'")
        
        self._compute(decomp_file=self.decomp_file)
        if alter:
            output_table = SystemSf(self.OutputDescription, self.P, self.P_default, datesim = self.P.datesim, country = self.country, num_table = self.num_table)
            output_table.set_inputs(input_table_alter, country = self.country)
            output_table.decomp_file = self.decomp_file
            output_table.disable(self.disabled_prestations)
            self.data = output_table.calculate()
            self.output_table = output_table
            
        if difference or self.reforme:
            self.data.difference(self.data_default)  
        
        return self.data, self.data_default
        
    def preproc_alter_scenario(self, input_table_alter):
        """
        Prepare the output values according to the OutputDescription definitions and 
        input_table when an alternative scenario is present
        
        Parameters
        ----------
        
        input_table_alter : TODO: complete
        input_table : TODO: complete
        """
        P_default = self.P_default     
        P         = self.P  
        
        self.output_table = SystemSf(self.OutputDescription, P, P_default, datesim = P.datesim, country = self.country)
        self.output_table.set_inputs(self.input_table, country = self.country)
                
        output_alter = SystemSf(self.OutputDescription, P, P_default, datesim = P.datesim, country = self.country)
        output_alter.set_inputs(input_table_alter, country = self.country)
    
        self.output_table.disable(self.disabled_prestations)
        output_alter.disable(self.disabled_prestations)
    
        return output_alter, self.output_table

    def get_results_dataframe(self, default = False, difference = False, index_by_code = False, ):
        """
        Formats data into a dataframe
        
        Parameters
        ----------
        default : boolean, default False
                  If True compute the default results
        difference :  boolean, default True
                      If True compute the difference between actual and default results
        index_by_code : boolean, default False
                  Index the row by the code instead of name of the different element
                  of decomp_file  
        
        Returns
        -------
        df : A DataFrame with computed data according to decomp_file
        """
        if self.data is None:
            self.compute(difference = difference)        
        
        data = self.data
        data_default = self.data_default
            
        data_dict = dict()
        index = []
        
        if default is True:
            data = data_default
        
        for row in data:
            if not row.desc in ('root'):
                if index_by_code is True:
                    index.append(row.code)
                    data_dict[row.code] = row.vals
                else:
                    index.append(row.desc)
                    data_dict[row.desc] = row.vals
                
        df = DataFrame(data_dict).T
        df = df.reindex(index)
        return df
        
    def draw_bareme(self, ax, graph_xaxis = None, legend = False, position = 1):
        """
        Draws a bareme on matplotlib.axes.Axes
        """
        reforme = self.reforme 
        alter = (self.alternative_scenario is not None)
        
        self.compute()
        data = self.data
        data_default = self.data_default
            
        data.setLeavesVisible()
        data_default.setLeavesVisible()
        if graph_xaxis is None:
            graph_xaxis = 'sal'
        if not alter:
            drawBareme(data, ax, graph_xaxis, reforme, data_default, legend, country = self.country)
        else:
            drawBaremeCompareHouseholds(data, ax, graph_xaxis, data_default, legend, country = self.country, position = position)
        
    def draw_taux(self, ax, graph_xaxis = None, legend = True):
        """
        Draws a bareme on matplotlib.axes.Axes object ax
        """
        reforme = self.reforme or (self.alternative_scenario is not None)
        self.compute()
        data, data_default = self.data, self.data_default
        
        data.setLeavesVisible()
        data_default.setLeavesVisible()
        if graph_xaxis is None:
            graph_xaxis = 'sal'
        drawTaux(data, ax, graph_xaxis, reforme, data_default, legend = legend, country = self.country)
        
    def draw_waterfall(self, ax):
        """
        Draws a waterfall on matplotlib.axes.Axes object ax
        """
        data, data_default = self.compute()
        del data_default
        data.setLeavesVisible()
        drawWaterfall(data, ax)
        
    
class SurveySimulation(Simulation):
    """
    A Simulation class tailored to deal with survey data
    """
    def __init__(self):
        super(SurveySimulation, self).__init__()
        self.descr = None
        self.survey_filename = None
    
    
    def set_config(self, **kwargs):
        """
        Configures the SurveySimulation
        
        Parameters
        ----------
        TODO:
        survey_filename
        num_table
        """
        # Setting general attributes and getting the specific ones
        specific_kwargs = self._set_config(**kwargs)

        for key, val in specific_kwargs.iteritems():      
            if hasattr(self, key):
                setattr(self, key, val)
     
        if self.survey_filename is None:
            if self.country is not None:
                if self.num_table == 1 :
                    filename = os.path.join(SRC_PATH, 'countries', self.country, 'data', 'survey.h5')
                else:
                    filename = os.path.join(SRC_PATH, 'countries', self.country, 'data', 'survey3.h5')
                                                   
            self.survey_filename = filename
        
        if self.num_table not in [1,3] :
            raise Exception("OpenFisca can be run with 1 or 3 tables only, "
                            " please, choose between both.") 
    
        if not isinstance(self.chunk, int):
            raise Exception("Chunk number must be an integer")
                
    def inflate_survey(self, inflators):
        """
        Inflate some variable of the survey data
        
        Parameters
        ----------
        inflators : dict or DataFrame 
                    keys or a variable column should contain the variables to 
                    inflate and values of the value column the value of the inflator
        """
        
        if isinstance(inflators, DataFrame):
            for varname in inflators['variable']:
                inflators.set_index('variable')
                inflator = inflators.get_value(varname, 'value')
                self.input_table.inflate(varname, inflator)
        if isinstance(inflators, dict):
            for varname, inflator in inflators.iteritems():
                self.input_table.inflate(varname, inflator)
                               
    def check_input_table(self):
        """
        Consistency check of survey input data
        """
        check_consistency = of_import('utils', 'check_consistency', self.country)
        check_consistency(self.input_table)

    def initialize_input_table(self):
        """
        Initialize the input_table for a survey based simulation
        """            
        self.clear()
        self._initialize_input_table()
        self._build_dicts(option = 'input_only')


    def compute(self):
        """
        Computes the output_table for a survey based simulation
        """
        self.initialize_input_table()
        if len(self.input_table.table)==0:
            self.input_table.load_data_from_survey(self.survey_filename,  
                                               num_table = self.num_table,
                                               subset=self.subset,
                                               print_missing=self.verbose)
            
        if self.chunk == 1:     
            self._compute()
        # Note: subset has already be applied
        else: 
            num = self.num_table
            #TODO: replace 'idmen' by something not france-specific : the biggest entity
            if num == 1:
                list_men = self.input_table.table['idmen'].unique()
            if num == 3:
                list_men = self.input_table.table3['ind']['idmen'].unique()
            
            len_tot = len(list_men)
            len_chunk = int(len_tot/self.chunk)+1
            

            for chunk in range(0, self.chunk):
                start= chunk * len_chunk
                end = (chunk + 1)* len_chunk

                subsimu = SurveySimulation()
                subsimu.__dict__ = self.__dict__.copy()
                subsimu.subset = list_men[start:end]
                subsimu.chunk = 1             
                subsimu.compute()
                simu_chunk = subsimu
                print("compute chunk %d / %d" %(chunk +1 ,self.chunk) )
                
                if self.output_table is not None:
                    self.output_table = self.output_table + simu_chunk.output_table
                else: 
                    self.output_table = simu_chunk.output_table
                    
            # as set_imput didn't run, we do it now        
            self.output_table.index = self.input_table.index
            self.output_table._inputs = self.input_table
            self.output_table._nrows = self.input_table._nrows       

    def aggregated_by_entity(self, entity = None, variables = None, all_output_vars = True,
                              all_input_vars = False, force_sum = False):
        """
        Generates aggregates at entity level
        
        Parameters
        ----------
        entity : string, default None 
                 one of the entities which list can be found in countries.country.__init__.py
                 when None the first entity of ENTITIES_INDEX is used
        variables : list
                 variables to aggregate
        all_output_vars : boolean, default True
                          If True select all output variables
        all_output_vars : boolean, default False
                          If True select all input variables
        Returns
        -------
        out_tables[0], out_tables[1] : tuple of DataFrame                  
        """
        WEIGHT = of_import(None, 'WEIGHT', self.country) # import WEIGHT from country.__init__.py
        
        if self.output_table is None:
            raise Exception('self.output_table should not be None')
  
        if entity is None:
            ENTITIES_INDEX = of_import(None, 'ENTITIES_INDEX', self.country) # import ENTITIES_INDEX from country.__init__.py
            entity = ENTITIES_INDEX[0]
            
        models = [self.output_table]
        if self.reforme is True:
            models.append(self.output_table_default) 
        
        out_tables = []
        
        for model in models:
            out_dct = {}
            inputs = model._inputs
            idx = entity
            people = None
            if self.num_table == 1:
                try:
                    enum = inputs.description.get_col('qui'+entity).enum
                    people = [x[1] for x in enum]         
                except:
                    people = None
 
            # TODO: too franco-centric. Change this !!  
            if entity is "ind":
                entity_id = "noi"
            else:
                entity_id = "id"+entity
            
            input_variables = set([WEIGHT, entity_id] )
            if all_input_vars:           
                input_variables = input_variables.union(set(inputs.col_names))
            if variables is not None:
                input_variables = input_variables.union( set(inputs.col_names).intersection(variables))
                output_variables = set(model.col_names).intersection(variables)    


            if all_output_vars:
                output_variables = set(model.col_names)
            
            varnames = output_variables.union(input_variables)
            for varname in varnames:
                if varname in model.col_names:
                    col = model.description.get_col(varname)
                    condition = (col._entity != entity) or (force_sum == True)
                    from src.lib.columns import EnumCol, EnumPresta
                    type_col_condition = not(isinstance(col, EnumCol) or isinstance(col, EnumPresta)) 
                    if condition and type_col_condition:
                        val = model.get_value(varname, entity=idx, opt = people, sum_ = True)    
                    else:
                        val = model.get_value(varname, entity=idx)
                
                elif varname in inputs.col_names:
                    val = inputs.get_value(varname, idx)
                else:
                    raise Exception('%s was not find in model nor in inputs' % varname)
                
                out_dct[varname] = val      
            
            out_tables.append(DataFrame(out_dct))
        
        if self.reforme is False:
            out_tables.append(None)
                
        return out_tables[0], out_tables[1]
        

    def get_variables_dataframe(self, variables=None, entity="ind"):
        """
        Get variables 
        """
        return self.aggregated_by_entity(entity = entity, variables = variables,
                                         all_output_vars = False,
                                         all_input_vars = False, force_sum = False)[0]
        

    def clear(self):
        """
        Clear the outputs table 
        """
        self.output_table = None
        self.output_table_default = None
        gc.collect()
        
    def save_output_table(self, name, filename):
        """
        Saves the output dataframe under default directory in an HDF store.
        
        Parameters
        ----------
        name : the name of the table inside the store
        filename : the name of the .h5 file where the table is stored. Created if not existant.
        """
        ERF_HDF5_DATA_DIR = os.path.join(SRC_PATH,'countries','france','data','erf')
        store = HDFStore(os.path.join(os.path.dirname(ERF_HDF5_DATA_DIR),filename+'.h5'))
        store.put(name, self.output_table.table)
        #store.put('col_'+ name, self.output_table.description.columns ) marche pas, erreur de type
        store.close()
        
#===============================================================================
# if __name__ == "__main__":
#     year = 2006
#     sim = SurveySimulation()
#     sim._set_config(year=year)
#     
#     sim.filename = os.path.join(SRC_PATH, 'countries', 'france', 'data', 'fichiertest.h5')
#     sim.set_param()
#     sim.compute()
#     sim.save_output_table('testundeux', 'fichiertestundeux')
#===============================================================================
        


