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
        self.set_simulation_axes(simulation)
        return simulation

    def set_simulation_axes(self, simulation):
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
                    array[axis['index']:: entity.step_size] = mesh.reshape(simulation.steps_count)
