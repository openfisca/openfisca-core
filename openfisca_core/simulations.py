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


class Simulation(object):
    compact_legislation = None
    date = None
    debug = False
    default_compact_legislation = None
    entities = None
    entity_by_column_name = None
    entity_by_key_singular = None
    steps_count = None
    tax_benefit_system = None

    def __init__(self, compact_legislation = None, date = None, debug = False, tax_benefit_system = None):
        assert date is not None
        self.date = date
        if debug:
            self.debug = True
        assert tax_benefit_system is not None
        self.tax_benefit_system = tax_benefit_system

        self.compact_legislation = compact_legislation \
            if compact_legislation is not None \
            else tax_benefit_system.get_compact_legislation(date)
        self.default_compact_legislation = tax_benefit_system.get_compact_legislation(date)

    def calculate(self, column_name, requested_columns_name = None):
        return self.compute(column_name, requested_columns_name = requested_columns_name).array

    def compute(self, column_name, requested_columns_name = None):
        return self.entity_by_column_name[column_name].compute(column_name, requested_columns_name)

    def set_entities(self, entities):
        self.entities = entities
        self.entity_by_column_name = dict(
            (column_name, entity)
            for entity in self.entities.itervalues()
            for column_name in entity.column_by_name.iterkeys()
            )
        self.entity_by_key_singular = dict(
            (entity.key_singular, entity)
            for entity in self.entities.itervalues()
            )

    def get_holder(self, column_name, default = UnboundLocalError):
        entity = self.entity_by_column_name[column_name]
        if default is UnboundLocalError:
            return entity.holder_by_name[column_name]
        return entity.holder_by_name.get(column_name, default)

    def get_or_new_holder(self, column_name):
        entity = self.entity_by_column_name[column_name]
        holder = entity.holder_by_name.get(column_name)
        if holder is None:
            holder = entity.new_holder(column_name)
        return holder
