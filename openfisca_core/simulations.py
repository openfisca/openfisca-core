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

from . import legislations, periods


class Simulation(periods.PeriodMixin):
    compact_legislation_by_period_cache = None
    debug = False
    debug_all = False  # When False, log only formula calls with non-default parameters.
    entity_by_column_name = None
    entity_by_key_plural = None
    entity_by_key_singular = None
    legislation_json = None
    persons = None
    reference_compact_legislation_by_period_cache = None
    reference_legislation_json = None
    steps_count = 1
    tax_benefit_system = None
    trace = False
    traceback = None

    def __init__(self, debug = False, debug_all = False, entity_class_by_key_plural = None, legislation_json = None,
            period = None, reference_legislation_json = None, tax_benefit_system = None, trace = False):
        assert period is not None
        self.period = period
        if debug:
            self.debug = True
        if debug_all:
            assert debug
            self.debug_all = True
        assert tax_benefit_system is not None
        self.tax_benefit_system = tax_benefit_system
        if trace:
            self.trace = True
            self.traceback = collections.OrderedDict()

        # Note: Since simulations are short-lived and must be fast, don't use weakrefs for cache.
        self.compact_legislation_by_period_cache = {}
        if legislation_json is not None:
            self.legislation_json = legislation_json
        self.reference_compact_legislation_by_period_cache = {}
        if reference_legislation_json is not None:
            self.reference_legislation_json = reference_legislation_json

        entity_class_by_key_plural = tax_benefit_system.entity_class_by_key_plural \
            if entity_class_by_key_plural is None \
            else entity_class_by_key_plural
        self.entity_by_key_plural = dict(
            (key_plural, entity_class(simulation = self))
            for key_plural, entity_class in entity_class_by_key_plural.iteritems()
            )
        self.entity_by_column_name = dict(
            (column_name, entity)
            for entity in self.entity_by_key_plural.itervalues()
            for column_name in entity.column_by_name.iterkeys()
            )
        self.entity_by_key_singular = dict(
            (entity.key_singular, entity)
            for entity in self.entity_by_key_plural.itervalues()
            )
        for entity in self.entity_by_key_plural.itervalues():
            if entity.is_persons_entity:
                self.persons = entity
                break

    def calculate(self, column_name, lazy = False, period = None, requested_formulas_by_period = None):
        if period is None:
            period = self.period
        return self.compute(column_name, period = period, lazy = lazy,
            requested_formulas_by_period = requested_formulas_by_period).array

    def compute(self, column_name, lazy = False, period = None, requested_formulas_by_period = None):
        if period is None:
            period = self.period
        return self.entity_by_column_name[column_name].compute(column_name, lazy = lazy, period = period,
            requested_formulas_by_period = requested_formulas_by_period)

    def get_compact_legislation(self, period):
        compact_legislation = self.compact_legislation_by_period_cache.get(period)
        if compact_legislation is None:
            legislation_json = self.legislation_json
            if legislation_json is None:
                compact_legislation = self.tax_benefit_system.get_compact_legislation(period)
            else:
                dated_legislation_json = legislations.generate_dated_legislation_json(legislation_json, period)
                compact_legislation = legislations.compact_dated_node_json(dated_legislation_json)
                if self.tax_benefit_system.preprocess_compact_legislation is not None:
                    self.tax_benefit_system.preprocess_compact_legislation(compact_legislation)
            self.compact_legislation_by_period_cache[period] = compact_legislation
        return compact_legislation

    def get_holder(self, column_name, default = UnboundLocalError):
        entity = self.entity_by_column_name[column_name]
        if default is UnboundLocalError:
            return entity.holder_by_name[column_name]
        return entity.holder_by_name.get(column_name, default)

    def get_or_new_holder(self, column_name):
        entity = self.entity_by_column_name[column_name]
        return entity.get_or_new_holder(column_name)

    def get_reference_compact_legislation(self, period):
        reference_compact_legislation = self.reference_compact_legislation_by_period_cache.get(period)
        if reference_compact_legislation is None:
            reference_legislation_json = self.reference_legislation_json
            if reference_legislation_json is None:
                reference_compact_legislation = self.tax_benefit_system.get_compact_legislation(period)
            else:
                reference_dated_legislation_json = legislations.generate_dated_legislation_json(
                    reference_legislation_json, period)
                reference_compact_legislation = legislations.compact_dated_node_json(reference_dated_legislation_json)
                if self.tax_benefit_system.preprocess_compact_legislation is not None:
                    self.tax_benefit_system.preprocess_compact_legislation(reference_compact_legislation)
            self.reference_compact_legislation_by_period_cache[period] = reference_compact_legislation
        return reference_compact_legislation

    def graph(self, column_name, edges, nodes, visited):
        self.entity_by_column_name[column_name].graph(column_name, edges, nodes, visited)


def average_tax_rate(simulation, target_column_name = None, varying_column_name = None):
    target = simulation.calculate(target_column_name)    # numerator
    varying = simulation.calculate(varying_column_name)  # denominator
    div = varying * (varying != 0) + (varying == 0)
    average_rate = (1 - target / div)
    return average_rate


def marginal_tax_rate(simulation, target_column_name = None, varying_column_name = None):
    target = simulation.calculate(target_column_name)    # numerator
    varying = simulation.calculate(varying_column_name)  # denominator
    marginal_rate = (1 - (target[:-1] - target[1:]) / (varying[:-1] - varying[1:]))
    return marginal_rate
