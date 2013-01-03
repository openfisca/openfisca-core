#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

"""
openFisca, Logiciel libre de simulation du système socio-fiscal français
Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

This file is part of openFisca.

    openFisca is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    openFisca is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with openFisca.  If not, see <http://www.gnu.org/licenses/>.
"""

import os

# Common views

uiList = ['graph', 'declaration', 'composition', 'logement',
          'page01', 'page02', 'page03', 'page04', 'page05', 'page06', 'page07', 
          'page08', 'page_isf', 'parametres', 'baremedialog']

commands = []
for ui in uiList:
    commands.append("pyuic4 -o views/ui_" + ui +".py ui/" + ui + ".ui")

country_views = {'tunisia' : ['composition']}

for country in country_views.iterkeys():
    for ui in country_views[country]:
        commands.append("pyuic4 -o countries/" + country + "/views/ui_" + ui +".py " + country + "/ui/" + ui + ".ui")

commands.append("pyrcc4 -o resources_rc.py resources.qrc")

for command in commands:
    print command
    os.system(command)

