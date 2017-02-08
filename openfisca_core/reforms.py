# -*- coding: utf-8 -*-

import copy
import collections
import json

from biryani.strings import deep_encode

from . import conv, legislations, periods
from .taxbenefitsystems import TaxBenefitSystem


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
        self.reference = reference
        self._legislation_json = reference.get_legislation()
        self.compact_legislation_by_instant_cache = reference.compact_legislation_by_instant_cache
        self.column_by_name = reference.column_by_name.copy()
        self.decomposition_file_path = reference.decomposition_file_path
        self.Scenario = reference.Scenario
        self.key = unicode(self.__class__.__name__)
        if not hasattr(self, 'apply'):
            raise Exception("Reform {} must define an `apply` function".format(self.key))
        self.apply()

    def __getattr__(self, attribute):
        return getattr(self.reference, attribute)

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
        reform_legislation_json, errors = legislations.validate_legislation_json(reform_legislation_json)
        if errors is not None:
            errors = conv.embed_error(reform_legislation_json, 'errors', errors)
            if errors is None:
                legislation_json_str = json.dumps(
                    deep_encode(reform_legislation_json),
                    ensure_ascii = False,
                    indent = 2,
                    )
                raise ValueError('The modified legislation_json of the reform "{}" is invalid: {}'.format(
                    self.key.encode('utf-8'), legislation_json_str))
            raise ValueError(u'{} for: {}'.format(
                unicode(json.dumps(errors, ensure_ascii = False, indent = 2, sort_keys = True)),
                unicode(json.dumps(reform_legislation_json, ensure_ascii = False, indent = 2)),
                ).encode('utf-8'))
        self._legislation_json = reform_legislation_json
        self.compact_legislation_by_instant_cache = {}


def update_legislation(legislation_json, path = None, period = None, value = None, start = None, stop = None):
    """
    Update legislation JSON with a value defined for a specific couple of period defined by
    its start and stop instant or a period object.

    Returns the modified `legislation_json`.

    This function does not modify its arguments.
    """
    assert value is not None
    if period is not None:
        assert start is None and stop is None, u'period parameter can\'t be used with start and stop'
        start = period.start
        stop = period.stop
    assert start is not None, u'start must be provided, or period'

    def build_node(node, path_index):
        if isinstance(node, collections.Sequence):
            return [
                build_node(child_node, path_index + 1) if path[path_index] == index else child_node
                for index, child_node in enumerate(node)
                ]
        elif isinstance(node, collections.Mapping):
            return collections.OrderedDict((
                (
                    key,
                    (
                        update_items(child_node, start, stop, value)
                        if path_index == len(path) - 1
                        else build_node(child_node, path_index + 1)
                        )
                    if path[path_index] == key
                    else child_node
                    )
                for key, child_node in node.iteritems()
                ))
        else:
            raise ValueError(u'Unexpected type for node: {!r}'.format(node))

    updated_legislation = build_node(legislation_json, 0)
    return updated_legislation


def update_items(items, start, stop, value):
    def is_contained_in(inner, outer):
        '''Returns True if `inner` is contained in `outer`.'''
        return inner['start'] >= outer['start'] and (
            outer.get('stop') is None or inner.get('stop') is not None and inner['stop'] <= outer['stop']
            )
    items = sorted(items, key=lambda item: item['start'])
    new_item = create_item(start, stop, value)
    split_items = list(split_item_containing_instant(start, items))
    if stop is not None:
        split_items = list(split_item_containing_instant(stop.offset(+1, 'day'), split_items))
    not_contained_items = list(filter(lambda item: not is_contained_in(item, new_item), split_items))
    if not_contained_items and not_contained_items[-1].get('stop') is None \
            and str(start) > not_contained_items[-1]['start']:
        last_not_contained_item = not_contained_items[-1].copy()  # Copy to avoid modifying `items` argument.
        last_not_contained_item['stop'] = str(start.offset(-1, 'day'))
        not_contained_items[-1] = last_not_contained_item
    new_items = sorted(not_contained_items + [new_item], key=lambda item: item['start'])
    return new_items


def create_item(start, stop, value):
    dict_items = []
    if start is not None:
        dict_items.append(('start', str(start)))
    if stop is not None:
        dict_items.append(('stop', str(stop)))
    dict_items.append(('value', value))
    return collections.OrderedDict(dict_items)


def split_item_containing_instant(instant, items):
    '''
    Returns `items` list updated so that the item containing `instant` is split.

    If `instant` is contained in an item, it will be the start instant of the matching item.
    '''
    assert instant is not None
    for item in items:
        item_start = periods.instant(item['start'])
        item_stop = item.get('stop')
        if item_stop is not None:
            item_stop = periods.instant(item_stop)
        if item_start < instant and (item_stop is None or instant < item_stop):
            yield create_item(
                item['start'],
                str(instant.offset(-1, 'day')),
                item['value'],
                )
            yield create_item(
                str(instant),
                item.get('stop'),
                item['value']
                )
        else:
            yield item
