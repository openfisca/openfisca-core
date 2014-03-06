# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
# https://github.com/openfisca
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
import xml.etree.ElementTree
import weakref

from . import conv, legislations, legislationsxml


__all__ = ['AbstractTaxBenefitSystem']


class AbstractTaxBenefitSystem(object):
    AGGREGATES_DEFAULT_VARS = None
    check_consistency = None
    column_by_name = None
    columns_name_tree_by_entity = None
    compact_legislation_by_date_str_cache = None
    CURRENCY = None
    DATA_DIR = None
    DATA_SOURCES_DIR = None
    DECOMP_DIR = None
    DEFAULT_DECOMP_FILE = None
    entities = None  # class attribute
    ENTITIES_INDEX = None  # class attribute
    FILTERING_VARS = None
    json_to_attributes = staticmethod(conv.pipe(
        conv.test_isinstance(dict),
        conv.struct({}),
        ))
    legislation_json = None
    PARAM_FILE = None  # class attribute
    prestation_by_name = None
    REFORMS_DIR = None
    REV_TYP = None
    REVENUES_CATEGORIES = None
    Scenario = None
    WEIGHT = None
    WEIGHT_INI = None

    def __init__(self):
        # Merge prestation_by_name into column_by_name, because it is no more used.
        # TODO: To delete once prestation_by_name is no more used.
        self.column_by_name.update(self.prestation_by_name)
        self.prestation_by_name = None

        self.compact_legislation_by_date_str_cache = weakref.WeakValueDictionary()

        legislation_tree = xml.etree.ElementTree.parse(self.PARAM_FILE)
        legislation_xml_json = conv.check(legislationsxml.xml_legislation_to_json)(legislation_tree.getroot())
        legislation_xml_json = conv.check(legislationsxml.validate_legislation_xml_json)(legislation_xml_json)
        _, self.legislation_json = legislationsxml.transform_node_xml_json_to_json(legislation_xml_json)

    def get_compact_legislation(self, date):
        date_str = date.isoformat()
        compact_legislation = self.compact_legislation_by_date_str_cache.get(date_str)
        if compact_legislation is None:
            dated_legislation_json = legislations.generate_dated_legislation_json(self.legislation_json, date)
            compact_legislation = legislations.compact_dated_node_json(dated_legislation_json)
            if self.preprocess_legislation_parameters is not None:
                self.preprocess_legislation_parameters(compact_legislation)
            self.compact_legislation_by_date_str_cache[date_str] = compact_legislation
        return compact_legislation

    @classmethod
    def json_to_instance(cls, value, state = None):
        attributes, error = conv.pipe(
            cls.json_to_attributes,
            conv.default({}),
            )(value, state = state or conv.default_state)
        if error is not None:
            return attributes, error
        return cls(**attributes), None


#class TaxBenefitSystem(DataTable):
#    def __init__(self, column_by_name, param, defaultParam = None, datesim = None, num_table = 1):
#        super(TaxBenefitSystem, self).__init__(column_by_name, datesim = datesim, num_table = num_table)
#        self._primitives = set()
#        self._param = param
#        self._default_param = defaultParam
#        self._inputs = None
#        self.index = None
#        if datesim is not None:
#            self.datesim = datesim

#        self.reset()
#        self.build()

#    def __add__(self, other):
#        """
#        Addition of two TaxBenefitSystem.
#        Add their output_table, iff it's the same simulation and only the survey differ
#        """
#        if not isinstance(other, TaxBenefitSystem):
#            raise Exception("Can only add a TaxBenefitSystem to a SystemSF")

#        assert self.num_table == other.num_table

#        if self.num_table == 1:
#            self.table = self.table.append(other.table, verify_integrity = True)

#        if self.num_table == 3:
#            assert(self.list_entities == other.list_entities)
#            for ent in self.list_entities:
#                self.table3[ent] = self.table3[ent].append(other.table3[ent])
#        return self

#    def build(self):
#        # Build the closest dependencies
#        for col in self.column_by_name.itervalues():
#            # Disable column if necessary
#            if col.start is not None and col.start > self.datesim or col.end is not None and col.end < self.datesim:
#                col.disabled = True
#            elif col.disabled:
#                del col.disabled

#            for input_varname in col.inputs:
#                input_col = self.column_by_name.get(input_varname)
#                if input_col is None:
#                    self._primitives.add(input_varname)
#                else:
#                    input_col.add_child(col)

#    def calculate(self):
#        if self.survey_data is not None or self.decomp_file is None:
#            return self.calculate_survey()
#        elif self.test_case is not None:
#            return self.calculate_test_case()
#        else:
#            raise Exception("survey_data or test_case attribute should not be None")

#    def calculate_prestation(self, col):
#        if col.calculated or col.disabled:
#            return

#        columns_name = set(self._inputs.column_by_name)
#        assert self._primitives <= columns_name, 'Calculating %s.\n %s are not set, use set_inputs before calling calculate.' \
#            '\n Primitives needed: %s,\n Inputs: %s' % (col.name, self._primitives - columns_name, self._primitives, columns_name)

#        entity = col.entity
#        assert entity is not None
#        required = set(col.inputs)

#        func_args = {}
#        for var in required:
#            if var in self._inputs.column_by_name:
#                if var in col._option:
#                    func_args[var] = self._inputs.get_value(var, entity, col._option[var])
#                else:
#                    func_args[var] = self._inputs.get_value(var, entity)

#        WEIGHT = self.WEIGHT
#        for parent_col in col._parents:
#            parent_name = parent_col.name
#            assert parent_name not in func_args or parent_name == WEIGHT, \
#                '%s provided twice: %s was found in primitives and in parents' % (col.name, col.name)
#            self.calculate_prestation(parent_col)
#            opt, freq = None, None

#            if parent_name in col._option:
#                opt = col._option[parent_name]

#            if parent_name in col._freq:
#                freq = col._freq[parent_name]
#                if freq[-1:] == "s":  # to return dict with all months or trims
#                    freqs = freq
#                    func_args[parent_name] = self.get_value(parent_name, entity, opt = opt, freqs = freqs)
#                else:
#                    converter = parent_col._frequency_converter(to_ = freq, from_ = parent_col.freq)
#                    func_args[parent_name] = converter(self.get_value(parent_name, entity, opt = opt))
#            else:
#                func_args[parent_name] = self.get_value(parent_name, entity, opt = opt)

#        if col._needParam:
#            func_args['_P'] = self._param
#            required.add('_P')

#        if col._needDefaultParam:
#            func_args['_defaultP'] = self._default_param
#            required.add('_defaultP')

#        provided = set(func_args.keys())
#        assert provided == required, '%s missing: %s needs %s but only %s were provided' % (
#            str(list(required - provided)), self._name, str(list(required)), str(list(provided)))

#        try:
#            self.set_value(col.name, col._func(**func_args), entity)
#        except:
#            print col.name
#            raise

#        col.calculated = True

#    def calculate_survey(self):
#        for col in self.column_by_name.itervalues():
#            try:
#                self.calculate_prestation(col)
#            except Exception as e:
#                print e
#                print col.name
#        return None

#    def calculate_test_case(self):
#        assert self.decomp_file is not None, "A decomposition XML file should be provided as attribute decomp_file"

#        decomp_doc = minidom.parse(self.decomp_file)
#        output_tree = decompositions.OutNode('root', 'root')
#        self.generate_output_tree(decomp_doc, output_tree)
#        return output_tree

#    def disable(self, disabled_prestations):
#        """Set some column as calculated so they are not evaluated and keep their default value."""
#        if disabled_prestations is not None:
#            for colname in disabled_prestations:
#                self.column_by_name[colname].calculated = True

#    def generate_output_tree(self, doc, output_tree, entity = 'men'):
#        if doc.childNodes:
#            for element in doc.childNodes:
#                if element.nodeType is not element.TEXT_NODE:
#                    code = element.getAttribute('code')
#                    desc = element.getAttribute('desc')
#                    cols = element.getAttribute('color')
#                    short = element.getAttribute('shortname')
#                    typv = element.getAttribute('typevar')
#                    if cols is not '':
#                        a = cols.rsplit(',')
#                        col = (float(a[0]), float(a[1]), float(a[2]))
#                    else: col = (0, 0, 0)
#                    if typv is not '':
#                        typv = int(typv)
#                    else: typv = 0
#                    child = decompositions.OutNode(code, desc, color = col, typevar = typv, shortname = short)
#                    output_tree.addChild(child)
#                    self.generate_output_tree(element, child, entity)
#        else:
#            inputs = self._inputs
#            enum = inputs.column_by_name.get('qui' + entity).enum
#            people = [x[1] for x in enum]
#            if output_tree.code in self.column_by_name:
#                self.calculate_prestation(self.column_by_name[output_tree.code])
#                val = self.get_value(output_tree.code, entity, opt = people, sum_ = True)
#            elif output_tree.code in inputs.column_by_name:
#                val = inputs.get_value(output_tree.code, entity, opt = people, sum_ = True)
#            else:
#                raise Exception('%s was not found in tax-benefit system nor in inputs' % output_tree.code)
#            # TODO: Detect NaN instead of replacing them.
#            np.nan_to_num(val)
#            output_tree.vals = val

#    def get_primitives(self):
#        """
#        Return socio-fiscal system primitives, ie variable needed as inputs
#        """
#        return self._primitives

#    def reset(self):
#        """
#        Sets all columns as not calculated
#        """
#        for col in self.column_by_name.itervalues():
#            if col.calculated:
#                del col.calculated

#    def set_inputs(self, inputs):
#        """
#        Set the input DataTable

#        Parameters
#        ----------
#        inputs : DataTable, required
#                 The input variable datatable
#        """
#        if not isinstance(inputs, DataTable):
#            raise TypeError('inputs must be a DataTable')
#        # check if all primitives are provided by the inputs
##        for prim in self._primitives:
##            if not prim in inputs.column_by_name:
##                raise Exception('%s is a required input and was not found in inputs' % prim)

#        # store inputs and indexes and nrows
#        self._inputs = inputs
#        self.index = inputs.index
#        self._nrows = inputs._nrows

#        self.survey_data = self._inputs.survey_data
#        self.test_case = self._inputs.test_case
#        # initialize the pandas DataFrame to store data

#        if self.num_table == 1:
#            dct = {}
#            for col in self.column_by_name.itervalues():
#                dflt = col._default
#                dtyp = col._dtype
#                dct[col.name] = np.ones(self._nrows, dtyp) * dflt
#            self.table = DataFrame(dct)

#        if self.num_table == 3:
#            self.table3 = {}
#            temp_dct = {'ind' : {}, 'foy' : {}, 'men' : {}, 'fam' : {}}
#            for col in self.column_by_name.itervalues():
#                dflt = col._default
#                dtyp = col._dtype
#                size = self.index[col.entity]['nb']
#                temp_dct[col.entity][col.name] = np.ones(size, dtyp) * dflt
#            for entity in self.list_entities:
#                self.table3[entity] = DataFrame(temp_dct[entity])

#        # Preprocess the input data according to country specification
#        if self.preproc_inputs is not None:
#            self.preproc_inputs(self._inputs)
