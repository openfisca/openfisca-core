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

from . import periods, simulations


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

    def new_simulation(self, scenario, debug = False, debug_all = False, trace = False):
        simulation = simulations.Simulation(
            debug = debug,
            debug_all = debug_all,
            entity_class_by_key_plural = self.entity_class_by_key_plural,
            legislation_json = self.legislation_json,
            period = scenario.period,
            tax_benefit_system = scenario.tax_benefit_system,
            trace = trace,
            )
        scenario.fill_simulation(simulation)
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


def find_item_at_date(items, date, nearest_in_period = None):
    """
    Find an item (a dict with start, stop, value key) at a specific date in a list of items which have each one
    a start date and a stop date.
    """
    instant = periods.instant(date)
    instant_str = str(instant)
    for item in items:
        if item['start'] <= instant_str <= item['stop']:
            return item
    if nearest_in_period is not None and nearest_in_period.start <= instant <= nearest_in_period.stop:
        earliest_item = min(items, key = lambda item: item['start'])
        if instant_str < earliest_item['start']:
            return earliest_item
        latest_item = max(items, key = lambda item: item['stop'])
        if instant_str > latest_item['stop']:
            return latest_item
    return None


def update_legislation(legislation_json, path, period, value):
    """
    Update legislation JSON with a value defined for a specific period.

    This function does not modify input parameters.
    """
    def build_node(root_node, path_index):
        if isinstance(root_node, collections.Sequence):
            return [
                build_node(node, path_index + 1) if path[path_index] == index else node
                for index, node in enumerate(root_node)
                ]
        elif isinstance(root_node, collections.Mapping):
            return collections.OrderedDict((
                (
                    key,
                    (
                        updated_legislation_items(node, period, value)
                        if path_index == len(path) - 1
                        else build_node(node, path_index + 1)
                        )
                    if path[path_index] == key
                    else node
                    )
                for key, node in root_node.iteritems()
                ))
        else:
            raise ValueError(u'Unexpected type for node: {!r}'.format(root_node))

    updated_legislation = build_node(legislation_json, 0)
    return updated_legislation


def updated_legislation_items(items, period, value):
    """
    Iterates items (a dict with start, stop, value key) and returns new items sorted by start date,
    according to these rules:
    * if the period matches no existing item, the new item is yielded as-is
    * if the period strictly overlaps another one, the new item is yielded as-is
    * if the period non-strictly overlaps another one, the existing item is partitioned, the period in common removed,
      the new item is yielded as-is and the parts of the existing item are yielded
    """
    assert isinstance(items, collections.Sequence)
    new_items = []
    new_item = collections.OrderedDict((
        ('start', str(period.start)),
        ('stop', str(period.stop)),
        ('value', value),
        ))
    new_item_start = period.start
    new_item_stop = period.stop
    overlapping_item = None
    for item in items:
        item_start = periods.instant(item['start'])
        item_stop = periods.instant(item['stop'])
        if period.intersection(item_start, item_stop) is not None:
            assert overlapping_item is None, u'Only one existing item can overlap the new item'
            overlapping_item = item
            new_items.append(new_item)
            if new_item_start > item_start:
                new_items.append(
                    collections.OrderedDict((
                        ('start', item['start']),
                        ('stop', str(new_item_start.offset(-1, 'day'))),
                        ('value', item['value']),
                        ))
                    )
            if new_item_stop < item_stop:
                new_items.append(
                    collections.OrderedDict((
                        ('start', str(new_item_stop.offset(1, 'day'))),
                        ('stop', item['stop']),
                        ('value', item['value']),
                        ))
                    )
        else:
            new_items.append(item)
    if overlapping_item is None:
        new_items.append(new_item)
    return sorted(new_items, key = lambda item: item['start'])
