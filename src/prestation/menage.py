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

import numpy as np
from Utils import OutNode
from xml.dom import minidom

def handleXml(doc, tree, fun, members):
    if doc.childNodes:
        for element in doc.childNodes:
            if element.nodeType is not element.TEXT_NODE:
                code = element.getAttribute('code')
                desc = element.getAttribute('desc')
                cols = element.getAttribute('color')
                short = element.getAttribute('shortname')
                typv = element.getAttribute('typevar')
                if cols is not '':
                    a = cols.rsplit(',')
                    col = (float(a[0]), float(a[1]), float(a[2]))
                else: col = (0,0,0)
                if typv is not '':
                    typv = int(typv)
                else: typv = 0
                child = OutNode(code, desc, color = col, typevar = typv, shortname=short)
                tree.addChild(child)
                handleXml(element, child, fun, members)
    else:
        tree.setVals(fun(members, tree.code, 'men', sumqui = True))

class Menage(object):
    
    def __init__(self, table):

        if True:
            self.taille = table.nbMen     
        else:
            self.taille = table.nbFam

        nbenfmax = table.nbenfmax 
        enfants = ['enf%d' % i for i in range(1, nbenfmax+1)]
        self.members = ['pref', 'cref'] + enfants

        self._doc = minidom.parse('data/totaux.xml')
        tree = OutNode('root', 'root')
        table.openReadMode()
        handleXml(self._doc, tree, table.get, self.members)

        nb_uci = self.UC(table)
        
        nivvie = OutNode('nivvie', 'Niveau de vie', shortname = 'Niveau de vie', vals = tree['revdisp'].vals/nb_uci, typevar = 2, parent= tree)
        tree.addChild(nivvie)
        table.close_()
        self.out = tree
                
    def UC(self, table):
        '''
        Calcul du nombre d'unité de consommation du ménage avec l'échelle de l'insee
        '''
        agems = np.array(table.get(self.members, 'agem', 'men', default = -9999))
        uc = np.ones(self.taille)
        for i in range(1,11):
            agem = agems[i]
            age = np.floor(agem/12)
            uc += ((0  <= age)*(age <= 14)*0.3 + 
                   (15 <= age)*(age <= 150)*0.5)
        return uc
        