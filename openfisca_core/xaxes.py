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


class XAxis(object):
    col_name = None
    label = None
    name = None
    typ_tot = None
    typ_tot_default = None

    def __init__(self, col_name = None, label = None, name = None, typ_tot = None, typ_tot_default = None):
        assert col_name is not None
        self.col_name = col_name
        assert name is not None
        self.label = label or name
        self.name = name
        assert typ_tot is not None
        self.typ_tot = typ_tot
        assert typ_tot_default is not None
        self.typ_tot_default = typ_tot_default
