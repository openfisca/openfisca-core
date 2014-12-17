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
# import weakref

from . import conv, legislations, legislationsxml


__all__ = [
    'AbstractTaxBenefitSystem',
    'LegacyTaxBenefitSystem',
    'LegislationLessTaxBenefitSystem',
    'XmlBasedTaxBenefitSystem',
    ]


class AbstractTaxBenefitSystem(object):
    _real_reference = None
    column_by_name = None  # computed at instance initialization from entities column_by_name
    compact_legislation_by_instant_cache = None
    consumers_by_variable_name = None  # for each variable, the list of (names of) prestations using this variable
    entity_class_by_key_plural = None
    legislation_json = None
    json_to_attributes = staticmethod(conv.pipe(
        conv.test_isinstance(dict),
        conv.struct({}),
        ))
    preprocess_compact_legislation = None  # To override with a method
    reference = None  # Reference tax-benefit system. Used only by reforms. Note: Reforms can be chained.
    reform_by_name = None
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
        self.column_by_name = column_by_name = collections.OrderedDict()
        for entity_class in self.entity_class_by_key_plural.itervalues():
            column_by_name.update(entity_class.column_by_name)

    def get_compact_legislation(self, instant):
        compact_legislation = self.compact_legislation_by_instant_cache.get(instant)
        if compact_legislation is None and self.legislation_json is not None:
            dated_legislation_json = legislations.generate_dated_legislation_json(self.legislation_json, instant)
            compact_legislation = legislations.compact_dated_node_json(dated_legislation_json)
            if self.preprocess_compact_legislation is not None:
                self.preprocess_compact_legislation(compact_legislation)
            self.compact_legislation_by_instant_cache[instant] = compact_legislation
        return compact_legislation

    def get_reference_compact_legislation(self, instant):
        reference = self.reference
        if reference is None:
            return self.get_compact_legislation(instant)
        return reference.get_reference_compact_legislation(instant)

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

    @property
    def real_reference(self):
        real_reference = self._real_reference
        if real_reference is None:
            reference = self.reference
            if reference is None:
                return self
            self._real_reference = real_reference = reference.real_reference
        return real_reference

    def set_variables_dependencies(self):
        if self.consumers_by_variable_name is None:
            self.consumers_by_variable_name = {}
            for column in self.column_by_name.itervalues():
                formula_class = column.formula_class
                if formula_class is not None:
                    formula_class.set_dependencies(column, self)


class LegislationLessTaxBenefitSystem(AbstractTaxBenefitSystem):
    pass


class XmlBasedTaxBenefitSystem(AbstractTaxBenefitSystem):
    """A tax-benefit sytem with legislation stored in a XML file."""
    legislation_xml_file_path = None  # class attribute or must be set before calling this __init__ method.

    def __init__(self, entity_class_by_key_plural = None):
        state = conv.State()
        legislation_json = conv.check(legislationsxml.xml_legislation_file_path_to_json)(
            self.legislation_xml_file_path, state = state)
        super(XmlBasedTaxBenefitSystem, self).__init__(
            entity_class_by_key_plural = entity_class_by_key_plural,
            legislation_json = legislation_json,
            )


class LegacyTaxBenefitSystem(XmlBasedTaxBenefitSystem):
    """The obsolete way of creating a TaxBenefitSystem. Don't use it anymore.

    In this kind of tax-benefit system, a lot of attributes are defined in class.
    """
    check_consistency = None
    columns_name_tree_by_entity = None
    entities = None  # class attribute

    def __init__(self):
        super(LegacyTaxBenefitSystem, self).__init__()
