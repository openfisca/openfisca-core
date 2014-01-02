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


# The model variables are created by each country-specific package (cf function init_country())
# Note: The variables below are not inited (to None) here, to ensure that execution will fail when they are used before
# OpenFisca country-specific package is properly inited.
__all__ = [
    'AGGREGATES_DEFAULT_VARS',
    'CURRENCY',
    'DATA_DIR',
    'DATA_SOURCES_DIR',
    'DECOMP_DIR',
    'DEFAULT_DECOMP_FILE',
    'ENTITIES_INDEX',
    'FILTERING_VARS',
    'InputDescription',
    'OutputDescription',
    'PARAM_FILE',
    'REFORMS_DIR',
    'REV_TYP',
    'REVENUES_CATEGORIES',
    'Scenario',
    'WEIGHT',
    'WEIGHT_INI',
    'x_axes',
    ]
