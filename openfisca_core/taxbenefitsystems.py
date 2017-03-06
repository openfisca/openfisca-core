# -*- coding: utf-8 -*-


import collections
import glob
from inspect import isclass
from os import path
from imp import find_module, load_module
import importlib
import logging

from setuptools import find_packages

from . import conv, legislations, legislationsxml
from variables import AbstractVariable
from scenarios import AbstractScenario
from formulas import neutralize_column

log = logging.getLogger(__name__)


class VariableNotFound(Exception):
    pass


class VariableNameConflict(Exception):
    """
    Exception raised when two variables with the same name are added to a tax and benefit system.
    """
    pass


class TaxBenefitSystem(object):
    """
    Represents the legislation.
    """
    _base_tax_benefit_system = None
    compact_legislation_by_instant_cache = None
    person_key_plural = None
    preprocess_legislation = None
    json_to_attributes = staticmethod(conv.pipe(
        conv.test_isinstance(dict),
        conv.struct({}),
        ))
    reference = None  # Reference tax-benefit system. Used only by reforms. Note: Reforms can be chained.
    Scenario = AbstractScenario
    cache_blacklist = None
    decomposition_file_path = None

    def __init__(self, entities, legislation_json = None):
        # TODO: Currently: Don't use a weakref, because they are cleared by Paste (at least) at each call.
        self.compact_legislation_by_instant_cache = {}  # weakref.WeakValueDictionary()
        self.column_by_name = collections.OrderedDict()
        self.automatically_loaded_variable = set()
        self.legislation_xml_info_list = []
        self._legislation_json = legislation_json

        self.entities = entities
        if entities is None or len(entities) == 0:
            raise Exception("A tax and benefit sytem must have at least an entity.")
        self.person_entity = [entity for entity in entities if entity.is_person][0]
        self.group_entities = [entity for entity in entities if not entity.is_person]

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

    @classmethod
    def json_to_instance(cls, value, state = None):
        attributes, error = conv.pipe(
            cls.json_to_attributes,
            conv.default({}),
            )(value, state = state or conv.default_state)
        if error is not None:
            return attributes, error
        return cls(**attributes), None

    def new_scenario(self):
        scenario = self.Scenario()
        scenario.tax_benefit_system = self
        return scenario

    def prefill_cache(self):
        pass

    def load_variable(self, variable_class, update = False):
        name = unicode(variable_class.__name__)
        variable_type = variable_class.__bases__[0]
        attributes = dict(variable_class.__dict__)

        existing_column = self.get_column(name)
        if existing_column:
            if update:
                attributes['reference'] = existing_column
            else:
                # Variables that are dependencies of others (trough a conversion column) can be loaded automatically
                # Is it still necessary ?
                if name in self.automatically_loaded_variable:
                    self.automatically_loaded_variable.remove(name)
                    return self.get_column(name)
                raise VariableNameConflict(
                    u'Variable "{}" is already defined. Use `update_variable` to replace it.'.format(name))

        # We pass the variable_class just for introspection.
        variable = variable_type(name, attributes, variable_class)
        # We need the tax and benefit system to identify columns mentioned by conversion variables.
        column = variable.to_column(self)
        self.add_column(column)

        return column

    def add_variable(self, variable):
        """
        Adds an OpenFisca variable to the tax and benefit system.

        :param variable: The variable to add. Must be a subclass of Variable or DatedVariable.

        :raises: :any:`VariableNameConflict` if a variable with the same name have previously been added to the tax and benefit system.
        """
        return self.load_variable(variable, update = False)

    def update_variable(self, variable):
        """
        Replaces an existing OpenFisca variable in the tax and benefit system by a new one.

        The new variable must have the same name than the old one.

        If no variable with the given name exists in the tax and benefit system, no error will be raised and the variable will be simply added.

        :param variable: Variable to add. Must be a subclass of Variable or DatedVariable.
        """
        return self.load_variable(variable, update = True)

    def add_variables_from_file(self, file_path):
        """
        Adds all OpenFisca variables contained in a given file to the tax and benefit system.
        """
        try:
            module_name = path.splitext(path.basename(file_path))[0]
            module_directory = path.dirname(file_path)
            module = load_module(module_name, *find_module(module_name, [module_directory]))
            potential_variables = [getattr(module, item) for item in dir(module) if not item.startswith('__')]
            for pot_variable in potential_variables:
                # We only want to get the module classes defined in this module (not imported)
                if isclass(pot_variable) and \
                        issubclass(pot_variable, AbstractVariable) and \
                        pot_variable.__module__.endswith(module_name):
                    self.add_variable(pot_variable)
        except:
            log.error(u'Unable to load OpenFisca variables from file "{}"'.format(file_path))
            raise

    def add_variables_from_directory(self, directory):
        """
        Recursively explores a directory, and adds all OpenFisca variables found there to the tax and benefit system.
        """
        py_files = glob.glob(path.join(directory, "*.py"))
        for py_file in py_files:
            self.add_variables_from_file(py_file)
        subdirectories = glob.glob(path.join(directory, "*/"))
        for subdirectory in subdirectories:
            self.add_variables_from_directory(subdirectory)

    def add_variables(self, *variables):
        """
        Adds a list of OpenFisca Variables to the `TaxBenefitSystem`.

        See also :any:`add_variable`
        """
        for variable in variables:
            self.add_variable(variable)

    def load_extension(self, extension):
        """
        Loads an extension to the tax and benefit system.
        """
        if path.isdir(extension):
            if find_packages(extension):
                # Load extension from a package directory
                extension_directory = path.join(extension, find_packages(extension)[0])
            else:
                # Load extension from a simple directory
                extension_directory = extension
        else:
            # Load extension from installed pip package
            try:
                package = importlib.import_module(extension)
                extension_directory = package.__path__[0]
            except ImportError:
                raise IOError(
                    "Error loading extension: {} is neither a directory, nor an installed package.".format(extension))

        self.add_variables_from_directory(extension_directory)
        param_file = path.join(extension_directory, 'parameters.xml')
        if path.isfile(param_file):
            self.add_legislation_params(param_file)

    def add_column(self, column):
        self.column_by_name[column.name] = column

    def get_column(self, column_name, check_existence = False):
        column = self.column_by_name.get(column_name)
        if not column and check_existence:
            raise VariableNotFound(u'Variable "{}" not found in current tax and benefit system'.format(column_name))
        return column

    def update_column(self, column_name, new_column):
        self.column_by_name[column_name] = new_column

    def neutralize_column(self, column_name):
        self.update_column(column_name, neutralize_column(self.get_column(column_name)))

    def add_legislation_params(self, path_to_xml_file, path_in_legislation_tree = None):
        """
        Adds an XML file to the legislation parameters.

        :param path_to_xml_file: Absolute path towards the XML legislation file.
        :param path_in_legislation_tree: Legislation path where the legislation node is added.

        Exemples:

        >>> self.add_legislation_params('/path/to/parameters/root.xml')
        >>> self.add_legislation_params('/path/to/parameters/taxes/income_tax.xml', 'taxes.income_tax')
        """
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

    def get_legislation(self, with_source_file_infos = False):
        if self._legislation_json is None:
            self.compute_legislation(with_source_file_infos = with_source_file_infos)
        return self._legislation_json
