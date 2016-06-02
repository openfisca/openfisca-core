# -*- coding: utf-8 -*-


import collections
from inspect import isclass
from os import path
from imp import find_module, load_module
# import weakref

from . import conv, legislations, legislationsxml
from openfisca_core import variables
from variables import AbstractVariable


__all__ = [
    'AbstractTaxBenefitSystem',
    'MultipleXmlBasedTaxBenefitSystem',
    'XmlBasedTaxBenefitSystem',
    ]


class AbstractTaxBenefitSystem(object):
    _base_tax_benefit_system = None
    column_by_name = None
    compact_legislation_by_instant_cache = None
    entity_class_by_key_plural = None
    legislation_json = None
    person_key_plural = None
    json_to_attributes = staticmethod(conv.pipe(
        conv.test_isinstance(dict),
        conv.struct({}),
        ))
    reference = None  # Reference tax-benefit system. Used only by reforms. Note: Reforms can be chained.
    Scenario = None
    cache_blacklist = None

    def __init__(self, entity_class_by_key_plural = None, legislation_json = None):
        # TODO: Currently: Don't use a weakref, because they are cleared by Paste (at least) at each call.
        self.compact_legislation_by_instant_cache = {}  # weakref.WeakValueDictionary()
        self.column_by_name = collections.OrderedDict()

        if entity_class_by_key_plural is not None:
            self.entity_class_by_key_plural = entity_class_by_key_plural
        assert self.entity_class_by_key_plural is not None

        if legislation_json is not None:
            self.legislation_json = legislation_json
        # Note: self.legislation_json may be None for simulators without legislation parameters.

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
        if traced_simulation is None:
            compact_legislation = self.compact_legislation_by_instant_cache.get(instant)
            if compact_legislation is None and self.legislation_json is not None:
                dated_legislation_json = legislations.generate_dated_legislation_json(self.legislation_json, instant)
                compact_legislation = legislations.compact_dated_node_json(dated_legislation_json)
                self.compact_legislation_by_instant_cache[instant] = compact_legislation
        else:
            dated_legislation_json = legislations.generate_dated_legislation_json(self.legislation_json, instant)
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

    def add_variable(self, variable_class, update = False):
        name = unicode(variable_class.__name__)
        variable_type = variable_class.__bases__[0]
        attributes = variable_class.__dict__

        if self.get_column(name) and not update:
            raise Exception('Variable {} is already defined. Use `update = True to replace it.'.format(name))

        # We pass the variable_class just for introspection for parsers.
        variable = variable_type(name, attributes, variable_class)
        # We need the tax benefit system to identify columns mentioned by reference or PersonToEntityColumn...
        column = variable.to_column(self)

        self.column_by_name[column.name] = column

    def add_variables_from_file(self, file):
        module_name = path.splitext(path.basename(file))[0]
        module_directory = path.dirname(file)
        module = load_module(module_name, *find_module(module_name, [module_directory]))

        potential_variables = [getattr(module, c) for c in dir(module) if not c.startswith('__')]
        for pot_variable in potential_variables:
            # We want to get the module classes that are subclasses of AbstractVariable,
            # but not the ones defined in variables, e.g. Variable, etc.
            if ((isclass(pot_variable) and
                 issubclass(pot_variable, AbstractVariable) and
                 pot_variable not in variables.__dict__.values())):
                self.add_variable(pot_variable)

    def add_variables(self, *variables):
        for variable in variables:
            self.add_variable(variable)

    def get_column(self, column_name):
        return self.column_by_name.get(column_name)


class XmlBasedTaxBenefitSystem(AbstractTaxBenefitSystem):
    """A tax and benefit sytem with legislation stored in a XML file."""
    legislation_xml_file_path = None  # class attribute or must be set before calling this __init__ method.
    preprocess_legislation = None

    def __init__(self, entity_class_by_key_plural = None):
        state = conv.default_state
        legislation_json = conv.check(legislationsxml.xml_legislation_file_path_to_json)(
            self.legislation_xml_file_path, state = state)
        if self.preprocess_legislation is not None:
            legislation_json = self.preprocess_legislation(legislation_json)
        super(XmlBasedTaxBenefitSystem, self).__init__(
            entity_class_by_key_plural = entity_class_by_key_plural,
            legislation_json = legislation_json,
            )


class MultipleXmlBasedTaxBenefitSystem(AbstractTaxBenefitSystem):
    """A tax and benefit sytem with legislation stored in many XML files."""
    legislation_xml_info_list = None  # class attribute or must be set before calling this __init__ method.
    preprocess_legislation = None

    def __init__(self, entity_class_by_key_plural = None):
        legislation_json = self.get_legislation_json(with_source_file_infos = False)
        super(MultipleXmlBasedTaxBenefitSystem, self).__init__(
            entity_class_by_key_plural = entity_class_by_key_plural,
            legislation_json = legislation_json,
            )

    def get_legislation_json(self, with_source_file_infos):
        state = conv.default_state
        xml_legislation_info_list_to_json = legislationsxml.make_xml_legislation_info_list_to_json(
            with_source_file_infos,
            )
        legislation_json = conv.check(xml_legislation_info_list_to_json)(self.legislation_xml_info_list, state = state)
        if self.preprocess_legislation is not None:
            legislation_json = self.preprocess_legislation(legislation_json)
        return legislation_json
