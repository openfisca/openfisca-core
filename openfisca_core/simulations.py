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
    default_compact_legislation = None
    entities = None
    entity_by_column_name = None
    tax_benefit_system = None

    def __init__(self, compact_legislation = None, date = None, tax_benefit_system = None):
        assert date is not None
        self.date = date
        assert tax_benefit_system is not None
        self.tax_benefit_system = tax_benefit_system

        self.compact_legislation = compact_legislation \
            if compact_legislation is not None \
            else tax_benefit_system.get_compact_legislation(date)
        self.default_compact_legislation = tax_benefit_system.get_compact_legislation(date)

    def compute(self, column_name, requested_columns_name = None):
        if requested_columns_name is None:
            requested_columns_name = set()
        else:
            assert column_name not in requested_columns_name, 'Infinite loop. Missing values for columns: {}'.format(
                u', '.join(sorted(requested_columns_name)).encode('utf-8'))
        return self.entity_by_column_name[column_name].compute(column_name, requested_columns_name)

    def set_entities(self, entities):
        self.entities = entities
        self.entity_by_column_name = dict(
            (column_name, entity)
            for entity in self.entities.itervalues()
            for column_name in entity.column_by_name.iterkeys()
            )

    def get_holder_by_name(self, column_name, default = UnboundLocalError):
        entity = self.entity_by_column_name[column_name]
        if default is UnboundLocalError:
            return entity.holder_by_name[column_name]
        return entity.holder_by_name.get(column_name, default)
