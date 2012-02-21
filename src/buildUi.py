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

uiList = ['mainwindow', 'graph', 'table', 
          'declaration', 'composition', 'logement', 'infocomp',
          'page01', 'page02A', 'page03A', 'page03B', 'page03C', 'page04A', 'page04B', 
          'page04C', 'parametres', 'baremedialog', 'aggregate_ouput']

commands = []
for ui in uiList:
    commands.append("pyuic4 -o views/ui_" + ui +".py ui/" + ui + ".ui")

commands.append("pyrcc4 -o resources_rc.py resources.qrc")

for command in commands:
    print command
    os.system(command)

