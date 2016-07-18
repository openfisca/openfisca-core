# -*- coding: utf-8 -*-

import copy
import collections

from . import legislations, periods
from taxbenefitsystems import TaxBenefitSystem


def compose_reforms(reforms, tax_benefit_system):
    """
    Compose reforms: the first reform is built with the given base tax-benefit system,
    then each one is built with the previous one as the reference.
    """
    def compose_reforms_reducer(memo, reform):
        reformed_tbs = reform(memo)
        return reformed_tbs
    final_tbs = reduce(compose_reforms_reducer, reforms, tax_benefit_system)
    return final_tbs


class Reform(TaxBenefitSystem):
    name = None

    def __init__(self, reference):
        self.entity_class_by_key_plural = reference.entity_class_by_key_plural
        self._legislation_json = reference.get_legislation()
        self.compact_legislation_by_instant_cache = reference.compact_legislation_by_instant_cache
        self.column_by_name = reference.column_by_name.copy()
        self.Scenario = reference.Scenario
        self.DEFAULT_DECOMP_FILE = reference.DEFAULT_DECOMP_FILE
        self.reference = reference
        self.key = unicode(self.__class__.__name__)
        if not hasattr(self, 'apply'):
            raise Exception("Reform {} must define an `apply` function".format(self.key))
        self.apply()

    @property
    def full_key(self):
        key = self.key
        assert key is not None, 'key was not set for reform {} (name: {!r})'.format(self, self.name)
        if self.reference is not None and hasattr(self.reference, 'key'):
            reference_full_key = self.reference.full_key
            key = u'.'.join([reference_full_key, key])
        return key

    def modify_legislation_json(self, modifier_function):
        """
        Copy the reference TaxBenefitSystem legislation_json attribute and return it.
        Used by reforms which need to modify the legislation_json, usually in the build_reform() function.
        Validates the new legislation.
        """
        reference_legislation_json = self.reference.get_legislation()
        reference_legislation_json_copy = copy.deepcopy(reference_legislation_json)
        reform_legislation_json = modifier_function(reference_legislation_json_copy)
        assert reform_legislation_json is not None, \
            'modifier_function {} in module {} must return the modified legislation_json'.format(
                modifier_function.__name__,
                modifier_function.__module__,
                )
        reform_legislation_json, error = legislations.validate_legislation_json(reform_legislation_json)
        assert error is None, \
            'The modified legislation_json of the reform "{}" is invalid, error: {}'.format(
                self.key, error).encode('utf-8')
        self._legislation_json = reform_legislation_json
        self.compact_legislation_by_instant_cache = {}


def update_legislation(legislation_json, path, period = None, value = None, start = None, stop = None):
    """
    Update legislation JSON with a value defined for a specific couple of period defined by
    its start and stop instant or a period object.

    This function does not modify input parameters.
    """
    assert value is not None
    if period is not None:
        assert start is None and stop is None, u'period parameter can\'t be used with start and stop'
        start = period.start
        stop = period.stop
    assert start is not None and stop is not None, u'start and stop must be provided, or period'

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
                        updated_legislation_items(node, start, stop, value)
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


def updated_legislation_items(items, start_instant, stop_instant, value):
    """
    This function is deprecated.

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
        ('start', start_instant),
        ('stop', stop_instant),
        ('value', value),
        ))
    inserted = False
    for item in items:
        item_start = periods.instant(item['start'])
        item_stop = item.get('stop')
        if item_stop is not None:
            item_stop = periods.instant(item_stop)
        if item_stop is not None and item_stop < start_instant or item_start > stop_instant:
            # non-overlapping items are kept: add and skip
            new_items.append(
                collections.OrderedDict((
                    ('start', item['start']),
                    ('stop', item['stop'] if item_stop is not None else None),
                    ('value', item['value']),
                    ))
                )
            continue

        if item_stop == stop_instant and item_start == start_instant:  # exact matching: replace
            if not inserted:
                new_items.append(
                    collections.OrderedDict((
                        ('start', str(start_instant)),
                        ('stop', str(stop_instant)),
                        ('value', new_item['value']),
                        ))
                    )
                inserted = True
            continue

        if item_start < start_instant and item_stop is not None and item_stop <= stop_instant:
            # left edge overlapping are corrected and new_item inserted
            new_items.append(
                collections.OrderedDict((
                    ('start', item['start']),
                    ('stop', str(start_instant.offset(-1, 'day'))),
                    ('value', item['value']),
                    ))
                )
            if not inserted:
                new_items.append(
                    collections.OrderedDict((
                        ('start', str(start_instant)),
                        ('stop', str(stop_instant)),
                        ('value', new_item['value']),
                        ))
                    )
                inserted = True

        if item_start < start_instant and (item_stop is None or item_stop > stop_instant):
            # new_item contained in item: divide, shrink left, insert, new, shrink right
            new_items.append(
                collections.OrderedDict((
                    ('start', item['start']),
                    ('stop', str(start_instant.offset(-1, 'day'))),
                    ('value', item['value']),
                    ))
                )
            if not inserted:
                new_items.append(
                    collections.OrderedDict((
                        ('start', str(start_instant)),
                        ('stop', str(stop_instant)),
                        ('value', new_item['value']),
                        ))
                    )
                inserted = True

            new_items.append(
                collections.OrderedDict((
                    ('start', str(stop_instant.offset(+1, 'day'))),
                    ('stop', item['stop'] if item_stop is not None else None),
                    ('value', item['value']),
                    ))
                )
        if item_start >= start_instant and item_stop is not None and item_stop < stop_instant:
            # right edge overlapping are corrected
            if not inserted:
                new_items.append(
                    collections.OrderedDict((
                        ('start', str(start_instant)),
                        ('stop', str(stop_instant)),
                        ('value', new_item['value']),
                        ))
                    )
                inserted = True

            new_items.append(
                collections.OrderedDict((
                    ('start', str(stop_instant.offset(+1, 'day'))),
                    ('stop', item['stop']),
                    ('value', item['value']),
                    ))
                )
        if item_start >= start_instant and item_stop is not None and item_stop <= stop_instant:
            # drop those
            continue

    return sorted(new_items, key = lambda item: item['start'])
