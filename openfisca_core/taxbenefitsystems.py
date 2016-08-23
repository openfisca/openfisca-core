# -*- coding: utf-8 -*-


import numpy as np
import collections
import glob
from inspect import isclass
from os import path
from imp import find_module, load_module
import inspect
# import weakref

from biryani import strings

from . import conv, legislations, legislationsxml, base_functions
from .variables import Variable


class VariableNotFound(Exception):
    pass


class VariableNameConflict(Exception):
    pass


class TaxBenefitSystem(object):
    compact_legislation_by_instant_cache = None
    preprocess_legislation = None
    person_key_plural = None
    json_to_attributes = staticmethod(conv.pipe(
        conv.test_isinstance(dict),
        conv.struct({}),
        ))
    DEFAULT_DECOMP_FILE = None

    def __init__(self, entities, legislation_json=None):
        # TODO: Currently: Don't use a weakref, because they are cleared by Paste (at least) at each call.
        self.compact_legislation_by_instant_cache = {}  # weakref.WeakValueDictionary()
        self.variable_class_by_name = collections.OrderedDict()
        self.automatically_loaded_variable = set()
        self.legislation_xml_info_list = []
        self._legislation_json = legislation_json

        if entities is None or len(entities) == 0:
            raise Exception("A tax benefit sytem must have at least an entity.")
        self.entities = entities

    @property
    def base_tax_benefit_system(self):
        base_tax_benefit_system = self._base_tax_benefit_system
        if base_tax_benefit_system is None:
            reference = self.reference
            if reference is None:
                return self
            self._base_tax_benefit_system = base_tax_benefit_system = reference.base_tax_benefit_system
        return base_tax_benefit_system

    def get_compact_legislation(self, instant, traced_simulation = None):
        legislation = self.get_legislation()
        if traced_simulation is None:
            compact_legislation = self.compact_legislation_by_instant_cache.get(instant)
            if compact_legislation is None and legislation is not None:
                dated_legislation_json = legislations.generate_dated_legislation_json(legislation, instant)
                compact_legislation = legislations.compact_dated_node_json(dated_legislation_json)
                self.compact_legislation_by_instant_cache[instant] = compact_legislation
        else:
            dated_legislation_json = legislations.generate_dated_legislation_json(legislation, instant)
            compact_legislation = legislations.compact_dated_node_json(
                dated_legislation_json,
                traced_simulation = traced_simulation,
                )
        return compact_legislation

    def get_reference_compact_legislation(self, instant, traced_simulation = None):
        reference = self.reference
        if reference is None:
            return self.get_compact_legislation(instant, traced_simulation = traced_simulation)
        return reference.get_reference_compact_legislation(instant, traced_simulation = traced_simulation)

    def load_variable_class(self, variable_class, update=False):
        name = unicode(variable_class.__name__)

        existing_variable_class = self.get_variable_class(name)

        if existing_variable_class and not update:
            # Variables that are dependencies of others (trough a conversion variable) can be loaded automatically
            if name in self.automatically_loaded_variable_class:
                self.automatically_loaded_variable_class.remove(name)
                return self.get_variable_class(name)
            raise VariableNameConflict(
                "Variable {} is already defined. Use `update_variable_class` to replace it.".format(name))

        if existing_variable_class and update:
            variable_class.reference = existing_variable_class

        # variable class
        assert not hasattr(variable_class, 'variable_type')
        setattr(variable_class, 'variable_type', variable_class.__name__)

        if not hasattr(variable_class, 'cerfa_field'):
            setattr(variable_class, 'cerfa_field', None)
        if not hasattr(variable_class, 'default'):
            setattr(variable_class, 'default', 0)
        if not hasattr(variable_class, 'dtype'):
            setattr(variable_class, 'dtype', float)
        if not hasattr(variable_class, 'end'):
            setattr(variable_class, 'end', None)
        if not hasattr(variable_class, 'entity'):
            setattr(variable_class, 'entity', None)  # Obsolete: To remove once build_..._couple() functions are no more used.
        if not hasattr(variable_class, 'entity_key_plural'):
            setattr(variable_class, 'entity_key_plural', None)
        if not hasattr(variable_class, 'entity_class'):
            setattr(variable_class, 'entity_class', None)
        if not hasattr(variable_class, 'formula_class'):
            setattr(variable_class, 'formula_class', None)
        if not hasattr(variable_class, 'is_period_size_independent'):
            setattr(variable_class, 'is_period_size_independent', False)  # When True, value of column doesn't depend from size of period (example: age)
        if not hasattr(variable_class, 'is_permanent'):
            setattr(variable_class, 'is_permanent', False)  # When True, value of column doesn't depend from time (example: ID, birth)
        if not hasattr(variable_class, 'label'):
            setattr(variable_class, 'label', None)
        if not hasattr(variable_class, 'law_reference'):
            setattr(variable_class, 'law_reference', None)  # Either a single reference or a list of references
        if not hasattr(variable_class, 'name'):
            setattr(variable_class, 'name', None)
        if not hasattr(variable_class, 'start'):
            setattr(variable_class, 'start', None)
        if not hasattr(variable_class, 'survey_only'):
            setattr(variable_class, 'survey_only', False)
        if not hasattr(variable_class, 'url'):
            setattr(variable_class, 'url', None)
        if not hasattr(variable_class, 'val_type'):
            setattr(variable_class, 'val_type', None)

        # column member
        if hasattr(variable_class, 'column'):
            # instantiate the column if not already done
            if inspect.isclass(variable_class.column):
                setattr(variable_class, 'column', variable_class.column())

            if variable_class.column.__class__.__name__ == 'BoolCol':
                setattr(variable_class, 'default', False)
                setattr(variable_class, 'dtype', np.bool)
                setattr(variable_class, 'is_period_size_independent', True)
                setattr(variable_class, 'json_type', 'Boolean')
            elif variable_class.column.__class__.__name__ == 'DateCol':
                setattr(variable_class, 'dtype', 'datetime64[D]')
                setattr(variable_class, 'is_period_size_independent', True)
                setattr(variable_class, 'json_type', 'Date')
                setattr(variable_class, 'val_type', 'date')
            elif variable_class.column.__class__.__name__ == 'FixedStrCol':
                setattr(variable_class, 'default', u'')
                setattr(variable_class, 'is_period_size_independent', True)
                setattr(variable_class, 'json_type', 'String')
                max_length = variable_class.column.get_params().get('max_length')
                setattr(variable_class, 'dtype', '|S{}'.format(max_length))

            elif variable_class.column.__class__.__name__ == 'FloatCol':
                setattr(variable_class, 'dtype', np.float32)
                setattr(variable_class, 'json_type', 'Float')
            elif variable_class.column.__class__.__name__ == 'IntCol':
                setattr(variable_class, 'dtype', np.int32)
                setattr(variable_class, 'json_type', 'Integer')
            elif variable_class.column.__class__.__name__ == 'StrCol':
                setattr(variable_class, 'default', u'')
                setattr(variable_class, 'dtype', object)
                setattr(variable_class, 'is_period_size_independent', True)
                setattr(variable_class, 'json_type', 'String')
            elif variable_class.column.__class__.__name__ == 'AgeCol':
                setattr(variable_class, 'default', -9999)
                setattr(variable_class, 'is_period_size_independent', True)
            elif variable_class.column.__class__.__name__ == 'EnumCol':
                setattr(variable_class, 'dtype', np.int16)
                setattr(variable_class, 'enum', None)
                setattr(variable_class, 'index_by_slug', None)
                setattr(variable_class, 'is_period_size_independent', True)
                setattr(variable_class, 'json_type', 'Enumeration')

            for k, v in variable_class.column.get_params().items():
                setattr(variable_class, k, v)
            if hasattr(variable_class, 'start_date'):
                setattr(variable_class, 'start', variable_class.start_date)
            if hasattr(variable_class, 'stop_date'):
                setattr(variable_class, 'end', variable_class.stop_date)
            assert not hasattr(variable_class, 'column_type')
            setattr(variable_class, 'column_type', variable_class.column.__class__.__name__)
            delattr(variable_class, 'column')

        # enum (if present in column)
        if hasattr(variable_class, 'enum'):
            if variable_class.enum is None:
                delattr(variable_class, 'enum')
            else:
                # This converters accepts either an item number or an item name.
                setattr(variable_class, 'index_by_slug', dict(
                    (strings.slugify(name), index)
                    for index, name in sorted(variable_class.enum._vars.iteritems())
                    ))

        # define base function
        if not hasattr(variable_class, 'base_function'):
            if variable_class.is_permanent:
                setattr(variable_class, 'base_function', base_functions.permanent_default_value)
            elif variable_class.is_period_size_independent:
                setattr(variable_class, 'base_function', base_functions.requested_period_last_value)
            else:
                setattr(variable_class, 'base_function', base_functions.requested_period_default_value)


        # rename 'entity_class' to 'entity'
        assert hasattr(variable_class, 'entity_class')
        setattr(variable_class, 'entity', variable_class.entity_class)
        delattr(variable_class, 'entity_class')

        self.variable_class_by_name[name] = variable_class
        return variable_class

    def add_variable_class(self, variable_class):
        return self.load_variable_class(variable_class, update = False)

    def update_variable(self, variable_class):
        return self.load_variable_class(variable_class, update = True)

    def add_variable_classes_from_file(self, file):
        module_name = path.splitext(path.basename(file))[0]
        module_directory = path.dirname(file)
        module = load_module(module_name, *find_module(module_name, [module_directory]))

        potential_variable_classes = [getattr(module, c) for c in dir(module) if not c.startswith('__')]
        for pot_variable_class in potential_variable_classes:
            # We only want to get the module classes defined in this module (not imported)
            if ((isclass(pot_variable_class) and
                 issubclass(pot_variable_class, Variable) and
                 pot_variable_class.__module__.endswith(module_name))):
                self.add_variable_class(pot_variable_class)

    def add_variable_classes_from_directory(self, directory):
        py_files = glob.glob(path.join(directory, "*.py"))
        for py_file in py_files:
            self.add_variable_classes_from_file(py_file)
        subdirectories = glob.glob(path.join(directory, "*/"))
        for subdirectory in subdirectories:
            self.add_variable_classes_from_directory(subdirectory)

    def add_variable_classes(self, *variables):
        for variable_class in variable_classes:
            self.add_variable_class(variable_class)

    def load_extension(self, extension_directory):
        if not path.isdir(extension_directory):
            raise IOError(
                "Error loading extension: the extension directory {} doesn't exist.".format(extension_directory))
        self.add_variable_classes_from_directory(extension_directory)
        param_file = path.join(extension_directory, 'parameters.xml')
        if path.isfile(param_file):
            self.add_legislation_params(param_file)

    def get_variable_class(self, variable_class_name, check_existence = False):
        variable_class = self.variable_class_by_name.get(variable_class_name)
        if not variable_class and check_existence:
            raise VariableNotFound(u'Variable "{}" not found in current tax benefit system'.format(variable_class_name))
        return variable_class

    def update_variable_class(self, variable_class_name, new_variable_class):
        self.variable_class_by_name[variable_class_name] = new_variable_class

    def neutralize_variable_class(self, variable_class_name):
        self.update_variable_class(variable_class_name, neutralize_variable_class(self.reference.get_variable_class(variable_class_name)))

    def add_legislation_params(self, path_to_xml_file, path_in_legislation_tree = None):
        if path_in_legislation_tree is not None:
            path_in_legislation_tree = path_in_legislation_tree.split('.')

        self.legislation_xml_info_list.append(
            (path_to_xml_file, path_in_legislation_tree)
            )
        # New parameters have been added, the legislation will have to be recomputed next time we need it.
        # Not very optimized, but today incremental building of the legislation is not implemented.
        self._legislation_json = None

    def compute_legislation(self, with_source_file_infos = False):
        state = conv.default_state
        xml_legislation_info_list_to_json = legislationsxml.make_xml_legislation_info_list_to_json(
            with_source_file_infos,
            )
        legislation_json = conv.check(xml_legislation_info_list_to_json)(self.legislation_xml_info_list, state = state)
        if self.preprocess_legislation is not None:
            legislation_json = self.preprocess_legislation(legislation_json)
        self._legislation_json = legislation_json

    def get_legislation(self):
        if self._legislation_json is None:
            self.compute_legislation()
        return self._legislation_json
