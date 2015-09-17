# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
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
import copy
import warnings

from . import formulas, legislations, periods, taxbenefitsystems


class AbstractReform(taxbenefitsystems.AbstractTaxBenefitSystem):
    """A reform is a variant of a TaxBenefitSystem, that refers to the real TaxBenefitSystem as its reference."""
    CURRENCY = None
    DECOMP_DIR = None
    DEFAULT_DECOMP_FILE = None
    key = None
    name = None

    def __init__(self):
        assert self.key is not None
        assert self.name is not None
        assert self.reference is not None, 'Reform requires a reference tax-benefit-system.'
        assert isinstance(self.reference, taxbenefitsystems.AbstractTaxBenefitSystem)
        self.Scenario = self.reference.Scenario

        if self.CURRENCY is None:
            currency = getattr(self.reference, 'CURRENCY', None)
            if currency is not None:
                self.CURRENCY = currency
        if self.DECOMP_DIR is None:
            decomp_dir = getattr(self.reference, 'DECOMP_DIR', None)
            if decomp_dir is not None:
                self.DECOMP_DIR = decomp_dir
        if self.DEFAULT_DECOMP_FILE is None:
            default_decomp_file = getattr(self.reference, 'DEFAULT_DECOMP_FILE', None)
            if default_decomp_file is not None:
                self.DEFAULT_DECOMP_FILE = default_decomp_file
        super(AbstractReform, self).__init__(
            entity_class_by_key_plural = self.entity_class_by_key_plural or self.reference.entity_class_by_key_plural,
            legislation_json = self.reference.legislation_json,
            )

    @property
    def full_key(self):
        key = self.key
        assert key is not None, 'key was not set for reform {} (name: {!r})'.format(self, self.name)
        if self.reference is not None:
            reference_key = getattr(self.reference, 'key', None)
            if reference_key is not None:
                key = u'.'.join([reference_key, key])
        return key

    def modify_legislation_json(self, modifier_function):
        """
        Copy the reference TaxBenefitSystem legislation_json attribute and return it.
        Used by reforms which need to modify the legislation_json, usually in the build_reform() function.
        Validates the new legislation.
        """
        reference_legislation_json = self.reference.legislation_json
        reference_legislation_json_copy = copy.deepcopy(reference_legislation_json)
        reform_legislation_json = modifier_function(reference_legislation_json_copy)
        assert reform_legislation_json is not None, \
            'modifier_function {} in module {} must return the modified legislation_json'.format(
                modifier_function.__name__,
                modifier_function.__module__,
                )
        reform_legislation_json, error = legislations.validate_legislation_json(reform_legislation_json)
        assert error is None, \
            u'The modified legislation_json of the reform "{}" is invalid, error: {}'.format(
                self.key, error).encode('utf-8')
        self.legislation_json = reform_legislation_json


def clone_entity_class(entity_class):
    class ReformEntity(entity_class):
        pass
    ReformEntity.column_by_name = entity_class.column_by_name.copy()
    return ReformEntity


def compose_reforms(build_functions_and_keys, tax_benefit_system):
    """
    Compose reforms: the first reform is built with the given base tax-benefit system,
    then each one is built with the previous one as the reference.
    """
    def compose_reforms_reducer(memo, item):
        build_reform, key = item
        reform = build_reform(tax_benefit_system = memo)
        assert isinstance(reform, AbstractReform), 'Reform {} returned an invalid value {!r}'.format(key, reform)
        return reform
    assert isinstance(build_functions_and_keys, list)
    reform = reduce(compose_reforms_reducer, build_functions_and_keys, tax_benefit_system)
    return reform


def make_reform(key, name, reference, decomposition_dir_name = None, decomposition_file_name = None,
        new_formulas = None):
    """
    Return a Reform class inherited from AbstractReform.

    Warning: new_formulas argument is deprecated.
    """
    assert isinstance(key, basestring)
    assert isinstance(name, basestring)
    assert isinstance(reference, taxbenefitsystems.AbstractTaxBenefitSystem)
    reform_entity_class_by_key_plural = {
        key_plural: clone_entity_class(entity_class)
        for key_plural, entity_class in reference.entity_class_by_key_plural.iteritems()
        }
    reform_entity_class_by_symbol = {
        entity_class.symbol: entity_class
        for entity_class in reform_entity_class_by_key_plural.itervalues()
        }
    reform_key = key
    reform_name = name
    reform_reference = reference

    class Reform(AbstractReform):
        _constructed = False
        DECOMP_DIR = decomposition_dir_name
        DEFAULT_DECOMP_FILE = decomposition_file_name
        entity_class_by_key_plural = reform_entity_class_by_key_plural
        key = reform_key
        name = reform_name
        reference = reform_reference

        def __init__(self):
            super(Reform, self).__init__()
            Reform._constructed = True

        @classmethod
        def formula(cls, column):
            assert not cls._constructed, \
                'You are trying to add a formula to a Reform but its constructor has already been called.'
            return formulas.make_reference_formula_decorator(
                entity_class_by_symbol = reform_entity_class_by_symbol,
                update = True,
                )(column)

        @classmethod
        def input_variable(cls, entity_class = None, **kwargs):
            assert not cls._constructed, \
                'You are trying to add an input variable to a Reform but its constructor has already been called.'
            # Ensure that entity_class belongs to reform (instead of reference tax-benefit system).
            entity_class = cls.entity_class_by_key_plural[entity_class.key_plural]
            assert 'update' not in kwargs
            kwargs['update'] = True
            return formulas.reference_input_variable(entity_class = entity_class, **kwargs)

    if new_formulas is not None:
        warnings.warn(
            "new_formulas is deprecated. Use reform.formula decorator instead on the formula classes, "
            "reform being the object returned by make_reform",
            DeprecationWarning,
            )
        assert isinstance(new_formulas, collections.Sequence)
        for new_formula in new_formulas:
            Reform.formula(new_formula)

    return Reform


# Legislation helpers


def update_legislation(legislation_json, path, period = None, value = None, start = None, stop = None):
    """
    This function is deprecated.

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
        item_stop = periods.instant(item['stop'])
        if item_stop < start_instant or item_start > stop_instant:  # non-overlapping items are kept: add and skip
            new_items.append(
                collections.OrderedDict((
                    ('start', item['start']),
                    ('stop', item['stop']),
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

        if item_start < start_instant and item_stop <= stop_instant:
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

        if item_start < start_instant and item_stop > stop_instant:
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
                    ('stop', item['stop']),
                    ('value', item['value']),
                    ))
                )
        if item_start >= start_instant and item_stop < stop_instant:
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
        if item_start >= start_instant and item_stop <= stop_instant:
            # drop those
            continue

    return sorted(new_items, key = lambda item: item['start'])
