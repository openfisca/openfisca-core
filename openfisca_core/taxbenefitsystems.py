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


import xml.etree.ElementTree
import weakref

from . import conv, legislations, legislationsxml


__all__ = ['AbstractTaxBenefitSystem']


class AbstractTaxBenefitSystem(object):
    check_consistency = None
    column_by_name = None
    columns_name_tree_by_entity = None
    compact_legislation_by_instant_cache = None
    entities = None  # class attribute
    ENTITIES_INDEX = None  # class attribute
    entity_class_by_key_plural = None  # class attribute
    entity_class_by_symbol = None  # class attribute
    json_to_attributes = staticmethod(conv.pipe(
        conv.test_isinstance(dict),
        conv.struct({}),
        ))
    legislation_json = None
    legislation_json_by_xml_file_path = {}  # class attribute
    PARAM_FILE = None  # class attribute
    preprocess_compact_legislation = None  # To override with a method
    prestation_by_name = None
    Scenario = None

    def __init__(self, legislation_json = None):
        # Merge prestation_by_name into column_by_name, because it is no more used.
        # TODO: To delete once prestation_by_name is no more used.
        self.column_by_name = column_by_name = self.column_by_name.copy()
        column_by_name.update(self.prestation_by_name)
        self.prestation_by_name = None

        for column in column_by_name.itervalues():
            formula_class = column.formula_constructor
            if formula_class is not None:
                formula_class.set_dependencies(column, column_by_name)

        self.compact_legislation_by_instant_cache = weakref.WeakValueDictionary()

        if legislation_json is None:
            legislation_xml_file_path = self.PARAM_FILE
            legislation_json = self.legislation_json_by_xml_file_path.get(legislation_xml_file_path)
            if legislation_json is None:
                legislation_tree = xml.etree.ElementTree.parse(legislation_xml_file_path)
                state = conv.State()
                legislation_xml_json = conv.check(legislationsxml.xml_legislation_to_json)(
                    legislation_tree.getroot(),
                    state = state,
                    )
                legislation_xml_json = conv.check(legislationsxml.validate_legislation_xml_json)(
                    legislation_xml_json,
                    state = state,
                    )
                _, legislation_json = legislationsxml.transform_node_xml_json_to_json(legislation_xml_json)
                self.legislation_json_by_xml_file_path[legislation_xml_file_path] = legislation_json
        self.legislation_json = legislation_json

    def get_compact_legislation(self, instant):
        compact_legislation = self.compact_legislation_by_instant_cache.get(instant)
        if compact_legislation is None:
            dated_legislation_json = legislations.generate_dated_legislation_json(self.legislation_json, instant)
            compact_legislation = legislations.compact_dated_node_json(dated_legislation_json)
            if self.preprocess_compact_legislation is not None:
                self.preprocess_compact_legislation(compact_legislation)
            self.compact_legislation_by_instant_cache[instant] = compact_legislation
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

    def new_scenario(self):
        scenario = self.Scenario()
        scenario.tax_benefit_system = self
        return scenario
