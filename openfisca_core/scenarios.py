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


import copy
import logging

from . import conv
from . import simulations


log = logging.getLogger(__name__)
N_ = lambda message: message


class AbstractScenario(object):
    compact_legislation = None
    date = None
    reform_by_name = None
    tax_benefit_system = None

    def __init__(self):
        self.reform_by_name = {}

    def add_reform(self, reform):
        self.reform_by_name[reform.name] = reform

    def add_reforms(self, reforms):
        for reform in reforms:
            self.add_reform(reform)

    def fill_simulation(self, simulation):
        """Implemented in child classes."""
        raise NotImplementedError

    def init_from_attributes(self, cache_dir = None, repair = False, **attributes):
        conv.check(self.make_json_or_python_to_attributes(cache_dir = cache_dir, repair = repair))(attributes)
        return self

    def make_json_or_python_to_attributes(self, cache_dir = None, repair = False):
        raise NotImplementedError  # TODO migrate here all the non test_case or survey specific stuff

    def new_simulation(self, debug = False, debug_all = False, reform_name = None, trace = False):
        if reform_name is None:
            entity_class_by_key_plural = None
            compact_legislation = self.compact_legislation
            reference_compact_legislation = None
        else:
            reform = self.reform_by_name[reform_name]
            entity_class_by_key_plural = reform.entity_class_by_key_plural
            compact_legislation = reform.compact_legislation
            reference_compact_legislation = reform.reference_compact_legislation
        simulation = simulations.Simulation(
            compact_legislation = compact_legislation,
            date = self.date,
            debug = debug,
            debug_all = debug_all,
            entity_class_by_key_plural = entity_class_by_key_plural,
            reference_compact_legislation = reference_compact_legislation,
            tax_benefit_system = self.tax_benefit_system,
            trace = trace,
            )
        self.fill_simulation(simulation)
        return simulation
