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


from openfisca_core import legislations


class Reform(object):
    _compact_legislation = None
    _reference_compact_legislation = None
    dated_legislation_json = None
    entity_class_by_key_plural = None
    label = None
    name = None
    reference_dated_legislation_json = None

    def __init__(self, dated_legislation_json = None, entity_class_by_key_plural = None, label = None, name = None,
                 reference_dated_legislation_json = None):
        assert name is not None, u"a name should be provided"
        self.dated_legislation_json = dated_legislation_json
        self.entity_class_by_key_plural = entity_class_by_key_plural
        self.label = label if label is not None else name
        self.name = name
        self.reference_dated_legislation_json = reference_dated_legislation_json

    @property
    def compact_legislation(self):
        if self._compact_legislation is None:
            self._compact_legislation = legislations.compact_dated_node_json(self.dated_legislation_json)
        return self._compact_legislation

    @property
    def reference_compact_legislation(self):
        if self._reference_compact_legislation is None:
            self._reference_compact_legislation = legislations.compact_dated_node_json(
                self.reference_dated_legislation_json
                )
        return self._reference_compact_legislation
