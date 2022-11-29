from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

import copy
import functools
import glob
import importlib
import importlib_metadata
import inspect
import logging
import os
import sys
import traceback
import typing

from openfisca_core import commons, periods, variables
from openfisca_core.entities import Entity
from openfisca_core.errors import VariableNameConflictError, VariableNotFoundError
from openfisca_core.parameters import ParameterNode
from openfisca_core.periods import Instant, Period
from openfisca_core.populations import Population, GroupPopulation
from openfisca_core.simulations import SimulationBuilder
from openfisca_core.types import ParameterNodeAtInstant
from openfisca_core.variables import Variable

log = logging.getLogger(__name__)


class TaxBenefitSystem:
    """Represents the legislation.

    It stores parameters (values defined for everyone) and variables (values
    defined for some given entity e.g. a person).

    Attributes:
        parameters: Directory containing the YAML parameter files.

    Args:
        entities: Entities used by the tax benefit system.

    """
    person_entity: Entity

    _base_tax_benefit_system = None
    _parameters_at_instant_cache: Dict[Instant, ParameterNodeAtInstant] = {}
    person_key_plural = None
    preprocess_parameters = None
    baseline = None  # Baseline tax-benefit system. Used only by reforms. Note: Reforms can be chained.
    cache_blacklist = None
    decomposition_file_path = None

    def __init__(self, entities: Sequence[Entity]) -> None:
        # TODO: Currently: Don't use a weakref, because they are cleared by Paste (at least) at each call.
        self.parameters: Optional[ParameterNode] = None
        self.variables: Dict[Any, Any] = {}
        self.open_api_config: Dict[Any, Any] = {}
        # Tax benefit systems are mutable, so entities (which need to know about our variables) can't be shared among them
        if entities is None or len(entities) == 0:
            raise Exception("A tax and benefit sytem must have at least an entity.")
        self.entities = [copy.copy(entity) for entity in entities]
        self.person_entity = [entity for entity in self.entities if entity.is_person][0]
        self.group_entities = [entity for entity in self.entities if not entity.is_person]
        for entity in self.entities:
            entity.set_tax_benefit_system(self)

    @property
    def base_tax_benefit_system(self):
        base_tax_benefit_system = self._base_tax_benefit_system
        if base_tax_benefit_system is None:
            baseline = self.baseline
            if baseline is None:
                return self
            self._base_tax_benefit_system = base_tax_benefit_system = baseline.base_tax_benefit_system
        return base_tax_benefit_system

    def instantiate_entities(self):
        person = self.person_entity
        members = Population(person)
        entities: typing.Dict[Entity.key, Entity] = {person.key: members}

        for entity in self.group_entities:
            entities[entity.key] = GroupPopulation(entity, members)

        return entities

    # Deprecated method of constructing simulations, to be phased out in favor of SimulationBuilder
    def new_scenario(self):
        class ScenarioAdapter(object):
            def __init__(self, tax_benefit_system):
                self.tax_benefit_system = tax_benefit_system

            def init_from_attributes(self, **attributes):
                self.attributes = attributes
                return self

            def init_from_dict(self, dict):
                self.attributes = None
                self.dict = dict
                self.period = dict.pop('period')
                return self

            def new_simulation(self, debug = False, opt_out_cache = False, use_baseline = False, trace = False):
                # Legacy from scenarios, used in reforms
                tax_benefit_system = self.tax_benefit_system
                if use_baseline:
                    while True:
                        baseline = tax_benefit_system.baseline
                        if baseline is None:
                            break
                        tax_benefit_system = baseline

                builder = SimulationBuilder()
                if self.attributes:
                    variables = self.attributes.get('input_variables') or {}
                    period = self.attributes.get('period')
                    builder.set_default_period(period)
                    simulation = builder.build_from_variables(tax_benefit_system, variables)
                else:
                    builder.set_default_period(self.period)
                    simulation = builder.build_from_entities(tax_benefit_system, self.dict)

                simulation.trace = trace
                simulation.debug = debug
                simulation.opt_out_cache = opt_out_cache

                return simulation

        return ScenarioAdapter(self)

    def prefill_cache(self):
        pass

    def load_variable(self, variable_class, update = False):
        name = variable_class.__name__

        # Check if a Variable with the same name is already registered.
        baseline_variable = self.get_variable(name)
        if baseline_variable and not update:
            raise VariableNameConflictError(
                'Variable "{}" is already defined. Use `update_variable` to replace it.'.format(name))

        variable = variable_class(baseline_variable = baseline_variable)
        self.variables[variable.name] = variable

        return variable

    def add_variable(self, variable: Variable) -> Variable:
        """Adds an OpenFisca variable to the tax and benefit system.

        Args:
            variable: The variable to add. Must be a subclass of Variable.

        Raises:
            openfisca_core.errors.VariableNameConflictError: if a variable with the same name have previously been added to the tax and benefit system.

        """
        return self.load_variable(variable, update = False)

    def replace_variable(self, variable: Variable) -> None:
        """Replaces an existing variable by a new one.

        The new variable must have the same name than the replaced one.

        If no variable with the given name exists in the Tax-Benefit system, no
        error will be raised and the new variable will be simply added.

        Args:
            variable: The variable to replace.

        """
        name = variable.__name__

        if self.variables.get(name) is not None:
            del self.variables[name]

        self.load_variable(variable, update = False)

    def update_variable(self, variable: Variable) -> Variable:
        """Update an existing variable in the Tax-Benefit system.

        All attributes of the updated variable that are not explicitly
        overridden by the new ``variable`` will stay unchanged.

        The new variable must have the same name than the updated one.

        If no variable with the given name exists in the tax and benefit
        system, no error will be raised and the new variable will be simply
        added.

        Args:
            variable: Variable to add. Must be a subclass of Variable.

        Returns:
            The added variable.

        """

        return self.load_variable(variable, update = True)

    def add_variables_from_file(self, file_path):
        """
        Adds all OpenFisca variables contained in a given file to the tax and benefit system.
        """
        try:
            file_name = os.path.splitext(os.path.basename(file_path))[0]

            #  As Python remembers loaded modules by name, in order to prevent collisions, we need to make sure that:
            #  - Files with the same name, but located in different directories, have a different module names. Hence the file path hash in the module name.
            #  - The same file, loaded by different tax and benefit systems, has distinct module names. Hence the `id(self)` in the module name.
            module_name = f"{id(self)}_{hash(os.path.abspath(file_path))}_{file_name}"

            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
            except NameError as e:
                logging.error(str(e) + ": if this code used to work, this error might be due to a major change in OpenFisca-Core. Checkout the changelog to learn more: <https://github.com/openfisca/openfisca-core/blob/master/CHANGELOG.md>")
                raise
            potential_variables = [getattr(module, item) for item in dir(module) if not item.startswith('__')]
            for pot_variable in potential_variables:
                # We only want to get the module classes defined in this module (not imported)
                if inspect.isclass(pot_variable) and issubclass(pot_variable, Variable) and pot_variable.__module__ == module_name:
                    self.add_variable(pot_variable)
        except Exception:
            log.error('Unable to load OpenFisca variables from file "{}"'.format(file_path))
            raise

    def add_variables_from_directory(self, directory):
        """
        Recursively explores a directory, and adds all OpenFisca variables found there to the tax and benefit system.
        """
        py_files = glob.glob(os.path.join(directory, "*.py"))
        for py_file in py_files:
            self.add_variables_from_file(py_file)
        subdirectories = glob.glob(os.path.join(directory, "*/"))
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

        :param str extension: The extension to load. Can be an absolute path pointing to an extension directory, or the name of an OpenFisca extension installed as a pip package.

        """
        # Load extension from installed pip package
        try:
            package = importlib.import_module(extension)
            extension_directory = package.__path__[0]
        except ImportError:
            message = os.linesep.join([traceback.format_exc(),
                                    'Error loading extension: `{}` is neither a directory, nor a package.'.format(extension),
                                    'Are you sure it is installed in your environment? If so, look at the stack trace above to determine the origin of this error.',
                                    'See more at <https://github.com/openfisca/openfisca-extension-template#installing>.'])
            raise ValueError(message)

        self.add_variables_from_directory(extension_directory)
        param_dir = os.path.join(extension_directory, 'parameters')
        if os.path.isdir(param_dir):
            extension_parameters = ParameterNode(directory_path = param_dir)
            self.parameters.merge(extension_parameters)

    def apply_reform(self, reform_path: str) -> "TaxBenefitSystem":
        """Generates a new tax and benefit system applying a reform to the tax and benefit system.

        The current tax and benefit system is **not** mutated.

        Args:
            reform_path: The reform to apply. Must respect the format *installed_package.sub_module.reform*

        Returns:
            TaxBenefitSystem: A reformed tax and benefit system.

        Example:

            >>> self.apply_reform('openfisca_france.reforms.inversion_revenus')

        """
        from openfisca_core.reforms import Reform
        try:
            reform_package, reform_name = reform_path.rsplit('.', 1)
        except ValueError:
            raise ValueError('`{}` does not seem to be a path pointing to a reform. A path looks like `some_country_package.reforms.some_reform.`'.format(reform_path))
        try:
            reform_module = importlib.import_module(reform_package)
        except ImportError:
            message = os.linesep.join([traceback.format_exc(),
                                    'Could not import `{}`.'.format(reform_package),
                                    'Are you sure of this reform module name? If so, look at the stack trace above to determine the origin of this error.'])
            raise ValueError(message)
        reform = getattr(reform_module, reform_name, None)
        if reform is None:
            raise ValueError('{} has no attribute {}'.format(reform_package, reform_name))
        if not issubclass(reform, Reform):
            raise ValueError('`{}` does not seem to be a valid Openfisca reform.'.format(reform_path))

        return reform(self)

    def get_variable(
            self,
            variable_name: str,
            check_existence: bool = False,
            ) -> Optional[Variable]:
        """
        Get a variable from the tax and benefit system.

        :param variable_name: Name of the requested variable.
        :param check_existence: If True, raise an error if the requested variable does not exist.
        """
        variables: Dict[str, Optional[Variable]] = self.variables
        variable: Optional[Variable] = variables.get(variable_name)

        if isinstance(variable, Variable):
            return variable

        if not isinstance(variable, Variable) and not check_existence:
            return variable

        raise VariableNotFoundError(variable_name, self)

    def neutralize_variable(self, variable_name: str):
        """
        Neutralizes an OpenFisca variable existing in the tax and benefit system.

        A neutralized variable always returns its default value when computed.

        Trying to set inputs for a neutralized variable has no effect except raising a warning.
        """
        self.variables[variable_name] = variables.get_neutralized_variable(self.get_variable(variable_name))

    def annualize_variable(
            self,
            variable_name: str,
            period: Optional[Period] = None,
            ) -> None:
        check: bool
        variable: Optional[Variable]
        annualised_variable: Variable

        check = bool(period)
        variable = self.get_variable(variable_name, check)

        if variable is None:
            raise VariableNotFoundError(variable_name, self)

        annualised_variable = variables.get_annualized_variable(variable)

        self.variables[variable_name] = annualised_variable

    def load_parameters(self, path_to_yaml_dir):
        """
        Loads the legislation parameter for a directory containing YAML parameters files.

        :param path_to_yaml_dir: Absolute path towards the YAML parameter directory.

        Example:

        >>> self.load_parameters('/path/to/yaml/parameters/dir')
        """

        parameters = ParameterNode('', directory_path = path_to_yaml_dir)

        if self.preprocess_parameters is not None:
            parameters = self.preprocess_parameters(parameters)

        self.parameters = parameters

    def _get_baseline_parameters_at_instant(self, instant):
        baseline = self.baseline
        if baseline is None:
            return self.get_parameters_at_instant(instant)
        return baseline._get_baseline_parameters_at_instant(instant)

    @functools.lru_cache()
    def get_parameters_at_instant(
            self,
            instant: Union[str, int, Period, Instant],
            ) -> Optional[ParameterNodeAtInstant]:
        """Get the parameters of the legislation at a given instant

        Args:
            instant: :obj:`str` formatted "YYYY-MM-DD" or :class:`~openfisca_core.periods.Instant`.

        Returns:
            The parameters of the legislation at a given instant.

        """

        key: Instant
        msg: str

        if isinstance(instant, Instant):
            key = instant

        elif isinstance(instant, Period):
            key = instant.start

        elif isinstance(instant, (str, int)):
            key = periods.instant(instant)

        else:
            msg = f"Expected an Instant (e.g. Instant((2017, 1, 1)) ). Got: {key}."
            raise AssertionError(msg)

        if self.parameters is None:
            return None

        return self.parameters.get_at_instant(key)

    def get_package_metadata(self) -> Dict[str, str]:
        """Gets metadata relative to the country package.

        Returns:
            A dictionary with the country package metadata

        Example:
            >>> tax_benefit_system.get_package_metadata()
            >>> {
            >>>    'location': '/path/to/dir/containing/package',
            >>>    'name': 'openfisca-france',
            >>>    'repository_url': 'https://github.com/openfisca/openfisca-france',
            >>>    'version': '17.2.0'
            >>>    }

        """

        # Handle reforms
        if self.baseline:
            return self.baseline.get_package_metadata()

        fallback_metadata = {
            'name': self.__class__.__name__,
            'version': '',
            'repository_url': '',
            'location': '',
            }

        module = inspect.getmodule(self)

        if module is None:
            return fallback_metadata

        if module.__package__ is None:
            return fallback_metadata

        package_name = module.__package__.split('.')[0]

        try:
            distribution = importlib_metadata.distribution(package_name)

        except importlib_metadata.PackageNotFoundError:
            return fallback_metadata

        source_file = inspect.getsourcefile(module)

        if source_file is not None:
            location = source_file.split(package_name)[0].rstrip("/")

        else:
            location = ""

        metadata = distribution.metadata

        return {
            'name': metadata["Name"].lower(),
            'version': distribution.version,
            'repository_url': metadata["Home-page"],
            'location': location,
            }

    def get_variables(
            self,
            entity: Optional[Entity] = None,
            ) -> Dict[str, Variable]:
        """Gets all variables contained in a tax and benefit system.

        Args:
            entity: If set, returns the variable defined for the given entity.

        Returns:
            A dictionary, indexed by variable names.

        """

        if not entity:
            return self.variables
        else:
            return {
                variable_name: variable
                for variable_name, variable in self.variables.items()
                # TODO - because entities are copied (see constructor) they can't be compared
                if variable.entity.key == entity.key
                }

    def clone(self):
        new = commons.empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.items():
            if key not in ('parameters', '_parameters_at_instant_cache', 'variables', 'open_api_config'):
                new_dict[key] = value
        for entity in new_dict['entities']:
            entity.set_tax_benefit_system(new)

        new_dict['parameters'] = self.parameters.clone()
        new_dict['_parameters_at_instant_cache'] = {}
        new_dict['variables'] = self.variables.copy()
        new_dict['open_api_config'] = self.open_api_config.copy()
        return new

    def entities_plural(self):
        return {entity.plural for entity in self.entities}

    def entities_by_singular(self):
        return {entity.key: entity for entity in self.entities}
