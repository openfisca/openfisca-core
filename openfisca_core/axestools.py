# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013 OpenFisca Team
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


from . import descriptions, model


class Xaxis(object):
    def __init__(self, col_name = None):
        super(Xaxis, self).__init__()

        self.col_name = col_name
        if self.col_name is not None:
            self.set(col_name)
            self.set_label()
        else:
            self.typ_tot = None
            self.typ_tot_default = None

    def set(self, col_name, name = None, typ_tot = None, typt_tot_default = None):
        """Set Xaxis attributes."""
        properties = model.XAXIS_PROPERTIES[col_name]
        self.name = properties['name']
        self.typ_tot = properties['typ_tot']
        self.typ_tot_default = properties['typ_tot_default']

    def set_label(self):
        description = descriptions.Description(model.InputDescription().columns)
        label2var, var2label, var2enum = description.builds_dicts()
        self.label = var2label[self.col_name]


def build_axes():
    return [
        Xaxis(col_name)
        for col_name in model.XAXIS_PROPERTIES
        ]
