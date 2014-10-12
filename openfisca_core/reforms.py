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


from . import simulations


class Reform(object):
    entity_class_by_key_plural = None
    label = None
    legislation_json = None
    name = None
    reference_legislation_json = None

    def __init__(self, entity_class_by_key_plural = None, label = None, legislation_json = None, name = None,
            reference_legislation_json = None):
        assert name is not None, u"a name should be provided"
        self.entity_class_by_key_plural = entity_class_by_key_plural
        self.label = label if label is not None else name
        self.legislation_json = legislation_json
        self.name = name
        self.reference_legislation_json = reference_legislation_json

    def new_simulation(self, debug = False, debug_all = False, scenario = None, trace = False):
        simulation = simulations.Simulation(
            debug = debug,
            debug_all = debug_all,
            legislation_json = self.legislation_json,
            period = scenario.period,
            tax_benefit_system = scenario.tax_benefit_system,
            trace = trace,
            )
        scenario.fill_simulation(simulation)
        scenario.set_simulation_axes(simulation)
        return simulation


def clone_entity_classes(entity_class_by_symbol, symbols):
    new_entity_class_by_symbol = {
        symbol: clone_entity_class(entity_class) if symbol in symbols else entity_class
        for symbol, entity_class in entity_class_by_symbol.iteritems()
        }
    return new_entity_class_by_symbol


def clone_entity_class(entity_class):
    class ReformEntity(entity_class):
        pass
    ReformEntity.column_by_name = entity_class.column_by_name.copy()
    return ReformEntity
