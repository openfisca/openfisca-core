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
    compact_legislation = None
    label = None
    name = None
    reference_dated_legislation_json = None
    reform_dated_legislation_json = None

    def __init__(self, label = None, name = None, reform_dated_legislation_json = None,
                 reference_dated_legislation_json = None):
        assert name is not None, u"a name should be provided"
        self.name = name
        if label is not None:
            self.label = label
        else:
            self.label = name
        if reform_dated_legislation_json is not None:
            self.reform_dated_legislation_json = reform_dated_legislation_json
        if reference_dated_legislation_json is not None:
            self.reference_dated_legislation_json = reference_dated_legislation_json

    @property
    def compact_legislation(self):
        return legislations.compact_dated_node_json(self.reform_dated_legislation_json)

    @property
    def reference_compact_legislation(self):
        return legislations.compact_dated_node_json(self.reference_dated_legislation_json)
