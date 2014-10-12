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


import logging

import numpy as np

from . import conv, periods, simulations


log = logging.getLogger(__name__)
N_ = lambda message: message


class AbstractScenario(periods.PeriodMixin):
    legislation_json = None
    tax_benefit_system = None

    @staticmethod
    def cleanup_period_in_json_or_python(value, state = None):
        if value is None:
            return None, None
        value = value.copy()
        if 'date' not in value:
            year = value.pop('year', None)
            if year is not None:
                value['date'] = year
        if 'period' not in value:
            date = value.pop('date', None)
            if date is not None:
                value['period'] = dict(
                    unit = u'year',
                    start = date,
                    )
        return value, None

    def fill_simulation(self, simulation):
        """Implemented in child classes."""
        raise NotImplementedError

    def init_from_attributes(self, cache_dir = None, repair = False, **attributes):
        conv.check(self.make_json_or_python_to_attributes(cache_dir = cache_dir, repair = repair))(attributes)
        return self

    def make_json_or_python_to_attributes(self, cache_dir = None, repair = False):
        raise NotImplementedError  # TODO: Migrate here all the non test_case or survey specific stuff.

    def new_simulation(self, debug = False, debug_all = False, trace = False):
        simulation = simulations.Simulation(
            debug = debug,
            debug_all = debug_all,
            legislation_json = self.legislation_json,
            period = self.period,
            tax_benefit_system = self.tax_benefit_system,
            trace = trace,
            )
        self.fill_simulation(simulation)
        return simulation

    def set_simulation_variables(self, simulation, variables_name_to_skip = None):
        column_by_name = self.tax_benefit_system.column_by_name
        steps_count = simulation.steps_count
        test_case = self.test_case
        if variables_name_to_skip is None:
            variables_name_to_skip = set()
        else:
            variables_name_to_skip = set(variables_name_to_skip)

        for entity_key_plural, entity in simulation.entity_by_key_plural.iteritems():
            used_columns_name = set(
                key
                for entity_member in test_case[entity_key_plural].itervalues()
                for key, value in entity_member.iteritems()
                if value is not None
                )
            for column_name, column in column_by_name.iteritems():
                if column.entity == entity.symbol and column_name in used_columns_name \
                        and column_name not in variables_name_to_skip:
                    cells_iter = (
                        cell if cell is not None else column.default
                        for cell in (
                            entity_member.get(column_name)
                            for step_index in range(steps_count)
                            for entity_member in test_case[entity_key_plural].itervalues()
                            )
                        )
                    array = np.fromiter(cells_iter, dtype = column.dtype) \
                        if column.dtype is not object else np.array(list(cells_iter), dtype = column.dtype)
                    holder = entity.get_or_new_holder(column_name)
                    holder.array = array

        if self.axes is not None:
            if len(self.axes) == 1:
                axis = self.axes[0]
                entity = simulation.entity_by_column_name[axis['name']]
                holder = simulation.get_or_new_holder(axis['name'])
                column = holder.column
                array = holder.array
                if array is None:
                    array = np.empty(entity.count, dtype = column.dtype)
                    array.fill(column.default)
                    holder.array = array
                array[axis['index']:: entity.step_size] = np.linspace(axis['min'], axis['max'], axis['count'])
            else:
                axes_linspaces = [
                    np.linspace(axis['min'], axis['max'], axis['count'])
                    for axis in self.axes
                    ]
                axes_meshes = np.meshgrid(*axes_linspaces)
                for axis, mesh in zip(self.axes, axes_meshes):
                    entity = simulation.entity_by_column_name[axis['name']]
                    holder = simulation.get_or_new_holder(axis['name'])
                    column = holder.column
                    array = holder.array
                    if array is None:
                        array = np.empty(entity.count, dtype = column.dtype)
                        array.fill(column.default)
                        holder.array = array
                    array[axis['index']:: entity.step_size] = mesh.reshape(steps_count)
