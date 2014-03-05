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

from . import conv


N_ = lambda message: message


def iter_decomposition_nodes(node_or_nodes, children_first = False):
    if isinstance(node_or_nodes, list):
        for node in nodes:
            for sub_node in iter_decomposition_nodes(node, children_first = children_first):
                yield sub_node
    else:
        if not children_first:
            yield node_or_nodes
        children = node_or_nodes.get('children')
        if children:
            for child_node in children:
                for sub_node in iter_decomposition_nodes(child_node, children_first = children_first):
                    yield sub_node
        if children_first:
            yield node_or_nodes


def make_validate_node_json(tax_benefit_system):
    def validate_node_json(node, state = None):
        if node is None:
            return None, None
        if state is None:
            state = conv.default_state
        validated_node, errors = conv.pipe(
            conv.test_isinstance(dict),
            conv.struct(
                {
                    '@context': conv.pipe(
                        conv.test_isinstance(basestring),
                        conv.make_input_to_url(full = True),
                        conv.test_equals(u'http://openfisca.fr/contexts/decomposition.jsonld'),
                        ),
                    '@type': conv.pipe(
                        conv.test_isinstance(basestring),
                        conv.cleanup_line,
                        conv.test_equals(u'Node'),
                        conv.not_none,
                        ),
                    'children': conv.pipe(
                        conv.test_isinstance(list),
                        conv.uniform_sequence(
                            validate_node_json,
                            drop_none_items = True,
                            ),
                        conv.empty_to_none,
                        ),
                    'code': conv.pipe(
                        conv.test_isinstance(basestring),
                        conv.cleanup_line,
                        conv.not_none,
                        ),
                    'color': conv.pipe(
                        conv.test_isinstance(list),
                        conv.uniform_sequence(
                            conv.pipe(
                                conv.test_isinstance(int),
                                conv.test_between(0, 255),
                                conv.not_none,
                                ),
                            ),
                        conv.test(lambda colors: len(colors) == 3, error = N_(u'Wrong number of colors in triplet.')),
                        ),
                    'comment': conv.pipe(
                        conv.test_isinstance(basestring),
                        conv.cleanup_text,
                        ),
                    'name': conv.pipe(
                        conv.test_isinstance(basestring),
                        conv.cleanup_line,
                        ),
                    'short_name': conv.pipe(
                        conv.test_isinstance(basestring),
                        conv.cleanup_line,
                        ),
                    'type': conv.pipe(
                        conv.test_isinstance(int),
                        conv.test_equals(2),
                        ),
                    },
                constructor = collections.OrderedDict,
                drop_none_values = 'missing',
                keep_value_order = True,
                ),
            )(node, state = state)
        if errors is not None:
            return validated_node, errors

        if not validated_node.get('children'):
            validated_node, errors = conv.struct(
                dict(
                    code = conv.test_in(tax_benefit_system.column_by_name),
                    ),
                default = conv.noop,
                )(validated_node, state = state)

        validated_node.pop('@context', None)  # Remove optional @context everywhere. It will be added to root node later.
        return validated_node, errors

    return validate_node_json
