# -*- coding: utf-8 -*-


import collections
# import weakref

from . import conv, legislations, legislationsxml


__all__ = [
    'AbstractTaxBenefitSystem',
    'MultipleXmlBasedTaxBenefitSystem',
    'XmlBasedTaxBenefitSystem',
    ]


class AbstractTaxBenefitSystem(object):
    _base_tax_benefit_system = None
    column_by_name = None  # computed at instance initialization from entities column_by_name
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

    def __init__(self, entity_class_by_key_plural = None, legislation_json = None):
        # TODO: Currently: Don't use a weakref, because they are cleared by Paste (at least) at each call.
        self.compact_legislation_by_instant_cache = {}  # weakref.WeakValueDictionary()

        if entity_class_by_key_plural is not None:
            self.entity_class_by_key_plural = entity_class_by_key_plural
        assert self.entity_class_by_key_plural is not None

        if legislation_json is not None:
            self.legislation_json = legislation_json
        # Note: self.legislation_json may be None for simulators without legislation parameters.

        # Now that classes of entities are defined, build a column_by_name by aggregating the column_by_name of each
        # entity class.
        assert self.column_by_name is None
        self.index_columns()

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

    def index_columns(self):
        self.column_by_name = column_by_name = collections.OrderedDict()
        for entity_class in self.entity_class_by_key_plural.itervalues():
            column_by_name.update(entity_class.column_by_name)
            if entity_class.is_persons_entity:
                self.person_key_plural = entity_class.key_plural

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
