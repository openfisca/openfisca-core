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

from famille import Famille
from foyer import IRPP
from menage import Menage
from datetime import datetime, date
from Config import CONF
class Systeme(object):
    '''
    Definit l'ordre dans lequel les impôts et prestations sont calculés.
    '''
    def __init__(self, population, P):
        '''
        Constructor
        '''
        self.year = population.year

        self.FA = Famille(population)

        self.F = IRPP(population)
        datesim = datetime.strptime(CONF.get('simulation', 'datesim'),"%Y-%m-%d").date()
        system = self.getSystem(datesim)
        for prestation in system:
            caller_class = prestation.im_class
            if caller_class == Famille: prestation(self.FA, P)
            if caller_class == IRPP  : 
                prestation(self.F, P.ir)
                del self.F

        del self.FA

        self.M = Menage(population)

    def getSystem(self, datesim):
        if datesim < date(2004, 1,1): # Transformation de l'APE et APJE en PAJE
            return [Famille.getRevEnf, Famille.AF,   IRPP.IR,     Famille.getRev, Famille.AEEH,  Famille.CF, 
                    Famille.APE,  Famille.APJE, Famille.CumulAPE_APJE_CF, Famille.ASF, Famille.ARS,  Famille.AL, 
                    Famille.MV,   Famille.AAH,  Famille.CAAH,   Famille.RMI,  Famille.AEFA,   
                    Famille.API ]
        elif datesim < date(2006, 1, 1): # Transformation du MV et de L'ASI en ASPA et ASI
            return [Famille.getRevEnf, Famille.AF,   IRPP.IR,      Famille.getRev, Famille.AEEH, Famille.CF,
                    Famille.PAJE, Famille.ASF,  Famille.ARS,    Famille.AL,   Famille.ASPA_ASI,   
                    Famille.AAH,  Famille.CAAH, Famille.RMI,    Famille.AEFA, Famille.API ]
        elif datesim < date(2009, 7, 1): # Transformation du RMI et de l'API en RSA
            return [Famille.getRevEnf, Famille.AF,   IRPP.IR,     Famille.getRev, Famille.AEEH,  Famille.CF,
                    Famille.PAJE, Famille.ASF,  Famille.ARS,    Famille.AL,   Famille.ASPA_ASI,
                    Famille.AAH,  Famille.CAAH, Famille.RMI,    Famille.AEFA, Famille.API]
        else:
            return [Famille.getRevEnf, Famille.AF,   IRPP.IR,      Famille.getRev, Famille.AEEH, Famille.CF,
                    Famille.PAJE, Famille.ASF,  Famille.ARS,    Famille.AL,   Famille.ASPA_ASI,
                    Famille.AAH,  Famille.CAAH, Famille.RSA,    Famille.AEFA ]

