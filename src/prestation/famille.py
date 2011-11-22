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

from __future__ import division
import numpy as np
from numpy import (round, sum, zeros, ones, maximum as max_, minimum as min_, 
                   ceil, where, logical_not as not_)
from datetime import datetime, date
from core.datatable import QUIFAM

CHEF = QUIFAM['chef']
PART = QUIFAM['part']

def famille_wrapper(enfant=True, crds=True):
    '''
    Décorateur pour tester:
      - si des enfants existent avant d exécuter la méthode
      - calculer les montant nets de crds si nécessaire
    '''
    def decorator(func): 
        def wrapper(self, P):
            name = getPrestationName(func)   # gère les mismatch entre noms de méthode et de variable stockant les montants
            brut_name = name + '_brut'
            if enfant: func(self, P)
                    
            brut_val  = getattr(self, brut_name)
            if crds:
                crds_val  = round(P.fam.af.crds*brut_val,2)
                tot_val   = brut_val - crds_val 
                setattr(self, name + '_crds', crds_val)
            else:
                tot_val   = brut_val 
                
            setattr(self, name + '_tot' ,  tot_val)
            self.population.openWriteMode()
            self.population.set(name, tot_val, 'fam', 'chef', table = 'output')
            self.population.close_()
                            
        return wrapper
    return decorator
    
def getPrestationName(func):
    name = func.__name__.lower() 
    if func.__name__[:4]=="paje": name = func.__name__[4:].lower()
    return name    

class Famille(object):

    def __init__(self,population):
        self.datesim = population.datesim
        super(Famille,self).__init__()

        self.population = population
        table = self.population        
        
        
        self.datesim = table.datesim
        self.taille = table.nbFam
        self.nbenfmax = table.nbenfmax

        table.openReadMode()
        
        self.nbpar = 1 + 1*(table.get('quifam', unit = 'fam', qui = 'part')==1)
        self.isol = self.nbpar == 1    # si parent isolé
        self.coup = self.nbpar == 2    # si couple (marié, pacsé ou non)
        # TODO : compléter
        self.maries = (table.get('statmarit', 'fam', 'part')==1)

        suffixe_enfants = ['%d' % i for i in range(1,self.nbenfmax+1)]
        suffixe = ['C', 'P'] + suffixe_enfants
        
        enfants = ['enf%d' % i for i in range(1,self.nbenfmax+1)]
        
        self.agemC, self.agemP = np.array(table.get('agem', 'fam', qui = ["chef", "part"], default = - 9999))
        self.ageC = np.floor(self.agemC/12)  # TODO mensualiser 
        self.ageP = np.floor(self.agemP/12)

        self.agem_enfants = np.array(table.get('agem', 'fam', qui = enfants, default = - 9999))
        
        people = ['chef', 'part'] + enfants
        invs   = table.get('inv', 'fam', people)
        for i in range(self.nbenfmax + 2):
            suf = suffixe[i]
            setattr(self, 'inv'+ suf, invs[i] )
            

        # TODO: Dans Population une fonction qui check s'il a plus d'une famille dans un ménage
        self.coloc = zeros(self.taille, dtype = bool)
        
        self.actC, self.actP = table.get('activite', 'fam', ['chef', 'part'])
        self.etuC   = self.actC == 2
        self.etuP   = self.actC == 2
        
        self.so       = table.get('so', 'fam', 'chef')        
        self.al_zone  = table.get('zone_apl', 'fam', 'chef')
        self.loyer    = table.get('loyer', 'fam', 'chef')
        
        table.close_()

    def getRevEnf(self, P):
        '''
        Récupère les revenus des enfants et teste s'ils sont plus 
        élevés que un pourcentage du smic valant P.af.seuil_rev_taux  
        '''
        nbh_travaillees = 151.67*12
        smic_annuel = P.cotsoc.gen.smic_h_b*nbh_travaillees
        enfants = ['enf%d' % i for i in range(1,self.nbenfmax+1)]
        self.population.openReadMode()   
        self.smic55 = (np.array(self.population.get('sal', 'fam', enfants, default = 0)) > P.fam.af.seuil_rev_taux*smic_annuel) 
        self.population.close_()    

    def getRev(self, P):
        '''
        Récupère les revenus qui provienne de la déclaration. Cette fonction ne doit être appellée 
        qu'après être passé par "Foyer"
        '''
        table = self.population
        table.openReadMode()
        # revenus categoriels du chef de famille et de son partenaire
        # TODO: ici, beaucoup de variable qui ne servent à rien 
        vardict = {'input': ['sal', 'hsup', 'cho', 'rst', 'alr'], 'output':['rto', 'revcap_bar', 'revcap_lib', 'etr', 'tspr', 'rpns', 'rfon', 'revColl', 'asf_elig', 'al_nbinv', 'div_rmi']}
        #, 'rag', 'ric', 'rnc', 'rac',       ]

        for tbl, varlist in vardict.iteritems():
            for cod in varlist:    
                temp = table.get(cod, 'fam', ['chef','part'], table = tbl)
                if cod in ['tspr', 'rpns', 'sal', 'etr', 'div_rmi', 'hsup']:
                    setattr(self, '%sC' % cod, temp[0])
                    setattr(self, '%sP' % cod, temp[1])
                setattr(self, cod, temp[0] + temp[1])

        table.close_()

def Couple():
    '''
    couple = 1 si couple marié sinon 0
    '''

def Concub():
    '''
    concub = 1 si couple 
    '''

def Ra_Rsa(sal, hsup, rpns, etr, div_rmi):
    '''
    Revenus d'activité au sens du Rsa
    '''
    return sal + hsup + rpns + etr + div_rmi

def Rev_PF(tspr, hsup, rpns):
    '''
    Base ressource individuelle des prestations familiales
    '''
    rev_pf  = tspr + hsup + rpns
    return rev_pf
    
def Br_PF(rev_pf, rev_coll, _option = {'rev_pf': [CHEF, PART]}):
    '''
    Base ressource des prestations familiales de la famille
    '''
    br_pf = rev_pf[CHEF] + rev_pf[PART] + rev_coll
    return br_pf
#    seuil_rev = 12*P.fam.af.bmaf_n_2
#    self.biact = (self.revChef >= seuil_rev) & (self.revPart >= seuil_rev)

def NbEnf2(self,ag1,ag2):
    '''
    Renvoie le nombre d'enfant à charge au sens des allocations familiales, 
    sous la forme d'une matrice [12,self.taille] avec le nombre d enfant dont l'âge
    est compris entre ag1 et ag2, à chaque mois de l'année.
    '''
#        Les allocations sont dues à compter du mois civil qui suit la naissance 
#        ag1==0 ou suivant les anniversaires ag1>0.  
#        Un enfant est reconnu à charge pour le versement des prestations 
#        jusqu'au mois précédant son age limite supérieur (ag2 + 1) mais 
#        le versement à lieu en début de mois suivant
    
    res = zeros((12,self.taille))
    for i in range(1,self.nbenfmax+1): 
        age = getattr(self, 'age%d' % i)
        smic55 = getattr(self, 'smic55_%d' % i)
        res += ((ag1 <=age) & (age <=ag2)) & not_(smic55) 
    return res

def getAgems(self):
    if hasattr(self, "agems"): return getattr(self, "agems")
    else:
        self.agems = np.array([m + self.agem_enfants for m in range(12)])
        return self.agems     

def getAges(self):
    if hasattr(self, "ages"): return getattr(self, "ages")
    else:
        self.ages  = np.floor(self.getAgems()/12) 
        return self.ages     

def NbEnf(self,ag1,ag2):
    '''
    Renvoie le nombre d'enfant à charge au sens des allocations familiales, 
    sous la forme d'une matrice [12,self.taille] avec le nombre d enfant dont l'âge
    est compris entre ag1 et ag2, à chaque mois de l'année.
    '''
#        Les allocations sont dues à compter du mois civil qui suit la naissance 
#        ag1==0 ou suivant les anniversaires ag1>0.  
#        Un enfant est reconnu à charge pour le versement des prestations 
#        jusqu'au mois précédant son age limite supérieur (ag2 + 1) mais 
#        le versement à lieu en début de mois suivant
    
    name = 'nbenf_%d_%d' % (ag1, ag2)

    if hasattr(self, name): 
        # print 'reload ' + name
        return getattr(self, name)
    else:
        ages   = self.getAges()
        # axe 0: mois
        # axe 1: enfants
        # axe 2: taille
        res = ( ((ag1 <=ages) & (ages <=ag2)) & not_(self.smic55)   ).sum(axis=1) 
        # print 'compute' + name 
        setattr(self, name, res)
        return res


def NbEnf_old(self, ag1, ag2, date_nais_lim=datetime(1970,1,1)):
    '''
    Renvoie le nombre d'enfant à charge au sens des allocations familiales, 
    sous la forme d'une matrice [12,self.taille] avec le nombre d enfant dont l'âge
    est compris entre ag1 et ag2, à chaque mois de l'année.
    '''
#        Les allocations sont dues à compter du mois civil qui suit la naissance 
#        ag1==0 ou suivant les anniversaires ag1>0.  
#        Un enfant est reconnu à charge pour le versement des prestations 
#        jusqu'au mois précédant son age limite supérieur (ag2 + 1) mais 
#        le versement à lieu en début de mois suivant
    
    name = 'nbenf_%d_%d' % (ag1, ag2)

    if hasattr(self, name): 
        # print 'reload ' + name
        return getattr(self, name)
    else:
        ages   = self.getAges()
        # axe 0: mois
        # axe 1: enfants 
        # axe 2: taille
        elig = not_(self.smic55) & (ages[0,:,:] < self.datesim.year - date_nais_lim.year)
        res = ( ((ag1 <=ages) & (ages <=ag2)) & elig).sum(axis=1) 
        # print 'compute' + name 
        setattr(self, name, res)
        return res
    

def aine(self, P):
    '''
    renvoi un vecteur avec le numéro de l'ainé (au sens des allocations 
    familiales) de chaque famille
    '''
    
    if hasattr(self, "aine"): 
        return getattr(self, "aine")
    else:
        res = zeros((12,self.taille) )
        ageaine = zeros((12,self.taille))
        ages  = self.getAges()
        for i in range(1,self.nbenfmax +1):
            age = ages[:,i-1,:]
            ispacaf = (P.af.age1 <=age) & (age <= P.af.age2)
            isaine  = ispacaf & (age > ageaine)
            ageaine = isaine*age + not_(isaine)*ageaine
            res     = isaine*i   + not_(isaine)*res
        self.aine = res 
        return res

def age_en_mois_benjamin(self, P, nmois=0):
    '''
    renvoi un vecteur (une entree pour chaque famille) avec l'age du benjamin. 
    Sont comptés les enfants qui peuvent devenir des enfants au sens  des allocations familiales 
    en moins de nmois  
    '''
    if hasattr(P.af,"age3"): agem_benjamin = zeros((12,self.taille))+P.af.age3*12
    else: agem_benjamin = zeros((12,self.taille))+P.af.age2*12
       
    agems = self.getAgems()
    for i in range(1,self.nbenfmax+1):
        agem = agems[:,i-1,:]
        ispacaf      = (-nmois <= agem) & (agem <= 12*P.af.age2)
        isbenjamin   = ispacaf & (agem < agem_benjamin)
        agem_benjamin = isbenjamin*agem + not_(isbenjamin)*agem_benjamin
    return agem_benjamin

    
def NbEnfA(self, ag1, ag2, P):
    '''
    Renvoie une matrice [12,self.taille] avec le nombre d'enfant (au sens des allocations familiales)
    dont les ages sont superieurs ou egaux a x et inferieur ou égaux à y à 
    l'exception de l'ainé des familles de deux enfants ou moins
    '''
    aine = self.aine(P)
    nbenf = self.NbEnf(P.af.age1,P.af.age2)
    res = zeros((12,self.taille)) 
    ages  = self.getAges()
    for i in range(1,self.nbenfmax+1):
        age  = ages[:,i-1,:]
        cond  = not_((aine == i)&(nbenf <= 2))
        res   += ((ag1 <=age) & (age <=ag2))*cond*1
    return res
    
def AF_Base(af_nbenf, _P):
    '''
    Allocations familiales - allocation de base
    '''
    P = _P.fam
    bmaf = P.af.bmaf    
#    af_nbenf      = self.NbEnf(P.af.age1,P.af.age2)

    # prestations familliales (brutes de crds)
    af_1enf      = round(bmaf*P.af.taux.enf1,2)
    af_2enf      = round(bmaf*P.af.taux.enf2,2)
    af_enf_supp  = round(bmaf*P.af.taux.enf3,2)

    af_base = (af_nbenf>=1)*af_1enf + (af_nbenf>=2)*af_2enf  + max_(af_nbenf-2,0)*af_enf_supp

    return af_base.sum(axis=0)
    
def AF_Majo(nbenf_maj1, nbenf_maj2, _P):
    # Date d'entrée en vigueur de la nouvelle majoration
    # enfants nés après le "1997-04-30"       
    bmaf = _P.fam.af.bmaf    
    P    = _P.fam.af.maj_age
    af_maj1       = round(bmaf*P.taux1,2)
    af_maj2       = round(bmaf*P.taux2,2)

    af_majo = nbenf_maj1*af_maj1 + nbenf_maj2*af_maj2

    return af_majo.sum(axis=0)

def AF_Forf(af_nbenf, nbenf_forf, _P):
    P = _P.fam
    bmaf = _P.fam.af.bmaf    
#    if hasattr(P.af,"age3"): af_nbenf_20 = self.NbEnf(P.af.age3,P.af.age3)
#    else: af_nbenf_20 = 0

    af_forfait   = round(bmaf*P.af.taux.forfait,2)
    af_ai20 = ((af_nbenf>=2)*nbenf_forf)*af_forfait
    
    return af_ai20.sum(axis=0)

def AF(af_base, af_majo, af_forf):
    return af_base + af_majo + af_forf

def CF(br_pf, cf_nbenf, isol, biact, _P):
    '''
    Complément familial
    Vous avez au moins 3 enfants à charge tous âgés de plus de 3 ans. 
    Vos ressources ne dépassent pas certaines limites. 
    Vous avez peut-être droit au Complément Familial à partir du mois 
    suivant les 3 ans du 3ème, 4ème, etc. enfant.
    
    # TODO: impossibilité de cumul cf avec apem ou apje
    # En théorie, il faut comparer les revenus de l'année n-2 à la bmaf de
    # l'année n-2 pour déterminer l'éligibilité avec le cf_seuil. Il faudrait
    # pouvoir déflater les revenus de l'année courante pour en tenir compte. 
    '''
    P = _P.fam
    bmaf = P.af.bmaf;
    bmaf2= P.af.bmaf_n_2;
#    cf_nbenf = self.NbEnf(P.cf.age1,P.cf.age2)
            
    cf_base_n_2 = P.cf.tx*bmaf2
    cf_base     = P.cf.tx*bmaf
    
    cf_plaf_tx = 1 + P.cf.plaf_tx1*min_(cf_nbenf,2) + P.cf.plaf_tx2*max_(cf_nbenf-2,0)
    cf_majo    = isol | biact
    cf_plaf    = P.cf.plaf*cf_plaf_tx + P.cf.plaf_maj*cf_majo
    cf_plaf2 = cf_plaf + 12*cf_base_n_2
    
    cf_brut = (cf_nbenf>=3)*((br_pf <= cf_plaf)*cf_base + 
                             (br_pf > cf_plaf)*max_(cf_plaf2- br_pf,0)/12.0 )
    
    return cf_brut

def ASF(rst, asf_nbenf, isol, asf_elig, _P):
    '''
    Allocation de soutien familial
    '''
    # L’ASF permet d’aider le conjoint survivant ou le parent isolé ayant la garde 
    # d’un enfant et les familles ayant à la charge effective et permanente un enfant 
    # orphelin.
    # Vous avez au moins un enfant à votre charge. Vous êtes son père ou sa mère et vous vivez seul(e),
    # ou vous avez recueilli cet enfant et vous vivez seul ou en couple.
    
    # Voir http://www.caf.fr/catalogueasf/bas.htm        
    # TODO: Ajouter orphelin recueilli, soustraction à l'obligation d'entretien (et date de celle-ci),
    # action devant le TGI pour complêter l'éligibilité               

    P = _P.fam
    
#    asf_nbenf = self.NbEnf(P.af.age1, P.af.age2)
    # TODO : gérer la mensualisation de l'ASF: pb de la pension alimentaire
    asf_nbenfa = asf_nbenf[11,:]

    asf_brut = round(isol*asf_elig*max_(0,asf_nbenfa*12*P.af.bmaf*P.asf.taux1 - rst),2)    
    asf_m    = round(isol*asf_elig*max_(0,asf_nbenf*P.af.bmaf*P.asf.taux1 - rst/12.0),2)
    
    return asf_brut

def ARS(br_pf, ars_nbenf, _P):
    '''
    Allocation de rentrée scolaire
    '''
    # On tient compte du fait qu'en cas de léger dépassement du plafond, une allocation dégressive 
    # (appelée allocation différentielle), calculée en fonction des revenus, peut être versée. 
    
    # nb, à partir de 2008, les taux sont différenciés suivant l'âge.

    P = _P.fam
    bmaf = P.af.bmaf
    # On prend l'âge en septembre
    enf_05    = NbEnf(P.ars.agep-1,P.ars.agep-1)[8,:]  # 6 ans avant le 31 janvier
    # Un enfant scolarisé qui n'a pas encore atteint l'âge de 6 ans 
    # avant le 1er février 2012 peut donner droit à l'ARS à condition qu'il 
    # soit inscrit à l'école primaire. Il faudra alors présenter un 
    # certificat de scolarité. 
    enf_primaire = enf_05 + NbEnf(P.ars.agep,P.ars.agec-1)[8,:]
    enf_college = NbEnf(P.ars.agec,P.ars.agel-1)[8,:]
    enf_lycee = NbEnf(P.ars.agel,P.ars.ages)[8,:]
    
    arsnbenf =   enf_primaire + enf_college + enf_lycee
    
    ars_plaf_res = P.ars.plaf*(1+ ars_nbenf*P.ars.plaf_enf_supp)
    arsbase  = bmaf*(P.ars.tx0610*enf_primaire + 
                     P.ars.tx1114*enf_college + 
                     P.ars.tx1518*enf_lycee )
    # Forme de l'ARS  en fonction des enfants a*n - (rev-plaf)/n                                             
    ars = max_(0,(ars_plaf_res + arsbase*arsnbenf - max_(br_pf, ars_plaf_res))/max_(1,arsnbenf))

    return ars*(ars>=P.ars.seuil_nv)

def PAJE(self, Param):
    '''
    Prestation d'accueil du jeune enfant
    '''
    self.pajeBase(Param)
    self.CumulPajeCf(Param) # TODO: Cumul avant la paje
    self.pajeNais(Param)
    self.pajeClca(Param)
    self.pajeClmg(Param)
    self.pajeColca(Param)

def pajeBase(br_pf, isol, biact, _P):
    ''' 
    Prestation d'acceuil du jeune enfant - allocation de base
    '''
    # TODO cumul des paje si et seulement si naissance multiples
    
    # TODO : théorie, il faut comparer les revenus de l'année n-2 à la bmaf de
    # l'année n-2 pour déterminer l'éligibilité avec le cf_seuil. Il faudrait
    # pouvoir déflater les revenus de l'année courante pour en tenir compte.
    
    P = _P.fam
    bmaf = P.af.bmaf
    bmaf2= P.af.bmaf_n_2

    base = round(P.paje.base.taux*bmaf,2)
    base2 = round(P.paje.base.taux*bmaf2,2)

    # L'allocation de base est versée jusqu'au dernier jour du mois civil précédant 
    # celui au cours duquel l'enfant atteint l'âge de 3 ans.
    
    nbenf = NbEnf(0,P.paje.base.age-1)
    
    plaf_tx = (nbenf>0) + P.paje.base.plaf_tx1*min_(nbenf,2) + P.paje.base.plaf_tx2*max_(nbenf-2,0)
    majo    = isol | biact
    plaf    = P.paje.base.plaf*plaf_tx + (plaf_tx>0)*P.paje.base.plaf_maj*majo
    plaf2   = plaf + 12*base2     # TODO vérifier l'aspect différentielle de la PAJE et le plaf2 de la paje
             
    paje_brut = (nbenf>0)*((br_pf <  plaf)*base + 
                           (br_pf >= plaf)*max_(plaf2-br_pf,0)/12) 
    
    # non cumulabe avec la CF, voir CumulPajeCF
    return paje_brut

def Paje_Nais(br_pf, isol, biact, _P):
    '''
    Prestation d'accueil du jeune enfant - Allocation de naissance
    '''
    P = _P.fam   
    bmaf = P.af.bmaf
    nais_prime = round(100*P.paje.nais.prime_tx*bmaf)/100
    
    # Versée au 7e mois de grossesse dans l'année
    # donc les enfants concernés sont les enfants entre -2 mois au 1er janvier
    # et -2 mois au 1er décembre
    # On calcule le mois de versement de la prime
    # TODO à mensualiser    
    benjamin = age_en_mois_benjamin(P,2)
    prime =  (benjamin==-2)
    nbnais    = sum(NbEnf(-1,-1)*prime,axis=0)

    # Et on compte le nombre d'enfants AF présents  pour le seul mois de la prime
    nbaf = sum(NbEnf(P.af.age1,P.af.age2)*prime,axis=0)
    nbenf = nbaf + nbnais   # On ajoute l'enfant à  naître;
    
    paje_plaf = P.paje.base.plaf
            
    plaf_tx = 1 + P.paje.base.plaf_tx1*min_(nbenf,2) + P.paje.base.plaf_tx2*max_(nbenf-2.,0)
    majo    = isol | biact
    nais_plaf    = paje_plaf*plaf_tx + majo
    elig = (br_pf <= nais_plaf)*(nbnais!=0)
    nais_brut = nais_prime*elig*(1+nbnais)
    
    return nais_brut  
    

def Paje_Clca( _P):
    '''
    Prestation d'accueil du jeune enfant - Complément de libre choix d'activité
    '''
    
    # http://www.caf.fr/wps/portal/particuliers/catalogue/metropole/paje
    paje     = (self.paje_brut_m >= 0)
    P = _P.fam

    # durée de versement :   
    # Pour un seul enfant à charge, le CLCA est versé pendant une période de 6 mois 
    # à partir de la naissance ou de la cessation des IJ maternité et paternité. 
    # A partir du 2ème enfant, il est versé jusqu’au mois précédant le 3ème anniversaire 
    # de l’enfant.
    
    # Calcul de l'année et mois de naisage_in_months( du cadet 
    # TODO: ajuster en fonction de la cessation des IJ etc
    # TODO les 6 mois sont codés en dur 
            
    benjamin = age_en_mois_benjamin(P)
   
    condition1 =(NbEnf(P.af.age1,P.af.age2)==1)*(benjamin>=0)*(benjamin<6)
    age = np.floor(benjamin/12)
    condition2 = ( age <= (P.paje.base.age-1))            
    condition = (NbEnf(0,P.af.age2)>=2)*condition2 + condition1 
    
    # TODO: rajouter ces infos aux parents et mensualiser
    inactif  = zeros((12,self.taille))
    # Temps partiel 1
    # Salarié: 
    # Temps de travail ne dépassant pas 50 % de la durée du travail fixée dans l'entreprise
    # VRP ou non salarié travaillant à temps partiel:
    # Temps de travail ne dépassant pas 76 heures par mois et un revenu professionnel mensuel inférieur ou égal à (smic_8.27*169*85 %)
    partiel1 = zeros((12,self.taille))
    
    # Temps partiel 2
    # Salarié:
    # Salarié: Temps de travail compris entre 50 et 80 % de la durée du travail fixée dans l'entreprise.
    # Temps de travail compris entre 77 et 122 heures par mois et un revenu professionnel mensuel ne dépassant pas
    #  (smic_8.27*169*136 %)

    partiel2  = zeros((12,self.taille))  

    clca_brut = (condition*P.af.bmaf)*(
                (not_(paje))*(inactif*P.paje.clca.sansab_tx_inactif   +
                            partiel1*P.paje.clca.sansab_tx_partiel1 +
                            partiel2*P.paje.clca.sansab_tx_partiel2)  +
                (paje)*(inactif*P.paje.clca.avecab_tx_inactif   +
                            partiel1*P.paje.clca.avecab_tx_partiel1 +
                            partiel2*P.paje.clca.avecab_tx_partiel2))
    self.clca_brut = sum(clca_brut,axis=0)
    
    self.clca_taux_plein =   (clca_brut>0)*inactif
    self.clca_taux_partiel = (clca_brut>0)*partiel1
            
    # TODO gérer les cumuls avec autres revenus et colca voir site caf

def pajeClmg(br_pf, _P):
    '''
    Prestation d accueil du jeune enfant - Complément de libre choix du mode de garde
    '''
    
#        Les conditions
#
#Vous devez :
#
#    avoir un enfant de moins de 6 ans né, adopté ou recueilli en vue d'adoption à partir du 1er janvier 2004
#    employer une assistante maternelle agréée ou une garde à domicile.
#    avoir une activité professionnelle min_
#        si vous êtes salarié cette activité doit vous procurer un revenu min_ de :
#            si vous vivez seul : une fois la BMAF
#            si vous vivez en couple  soit 2 fois la BMAF
#        si vous êtes non salarié, vous devez être à jour de vos cotisations sociales d'assurance vieillesse
#
#Vous n'avez pas besoin de justifier d'une activité min_ si vous êtes :
#
#    bénéficiaire de l'allocation aux adultes handicapés (Aah)
#    au chômage et bénéficiaire de l'allocation d'insertion ou de l'allocation de solidarité spécifique
#    bénéficiaire du Revenu de solidarité active (Rsa), sous certaines conditions de ressources étudiées par votre Caf, et inscrit dans une démarche d'insertion
#    étudiant (si vous vivez en couple, vous devez être tous les deux étudiants).
#
#Autres conditions à remplir : Assistante maternelle agréée     Garde à domicile
#Son salaire brut ne doit pas dépasser par jour de garde et par enfant 5 fois le montant du Smic horaire brut, soit au max_ 45,00 €.     Vous ne devez pas bénéficier de l'exonération des cotisations sociales dues pour la personne employée.
#
# 
    # TODO condition de revenu minimal
    elig = zeros((12,self.taille)) 
    empl_dir =zeros((12,self.taille))
    ass_mat = zeros((12,self.taille))
    gar_dom = zeros((12,self.taille))
    
    P = _P.fam
    nbenf = NbEnf(P.af.age1,P.af.age2)
    seuil1 = P.paje.clmg.seuil11*(nbenf==1) + P.paje.clmg.seuil12*(nbenf>=2) + max_(nbenf-2,0)*P.paje.clmg.seuil1sup
    seuil2 = P.paje.clmg.seuil21*(nbenf==1) + P.paje.clmg.seuil22*(nbenf>=2) + max_(nbenf-2,0)*P.paje.clmg.seuil2sup

#        Si vous bénéficiez du Clca taux partiel (= vous travaillez entre 50 et 80% de la durée du travail fixée dans l'entreprise), 
#        vous cumulez intégralement le Clca et le Cmg. 
#        Si vous bénéficiez du Clca taux partiel (= vous travaillez à 50% ou moins de la durée 
#        du travail fixée dans l'entreprise), le montant des plafonds Cmg est divisé par 2.
    seuil1 = seuil1*(1-.5*self.clca_taux_partiel)
    seuil2 = seuil2*(1-.5*self.clca_taux_partiel)
    
    clmg_brut = P.af.bmaf*((NbEnf(0,P.paje.clmg.age1-1)>0) + 
                           0.5*(NbEnf(P.paje.clmg.age1,P.paje.clmg.age2-1)>0) 
                           )*(
        empl_dir*(
            (br_pf < seuil1)*P.paje.clmg.empl_dir1 +
            ((br_pf >= seuil1) & (br_pf < seuil2) )*P.paje.clmg.empl_dir2 +
            (br_pf >= seuil2)*P.paje.clmg.empl_dir3) +
        ass_mat*(
            (br_pf < seuil1)*P.paje.clmg.ass_mat1 +
            ((br_pf >= seuil1) & (br_pf < seuil2) )*P.paje.clmg.ass_mat2 +
            (br_pf >= seuil2)*P.paje.clmg.ass_mat3)  +
        gar_dom*(
            (br_pf < seuil1)*P.paje.clmg.domi1 +
            ((br_pf >= seuil1) & (br_pf < seuil2) )*P.paje.clmg.domi2 +
            (br_pf >= seuil2)*P.paje.clmg.domi3))        

    # TODO: connecter avec le crédit d'impôt

#        Si vous bénéficiez du Clca taux plein (= vous ne travaillez plus ou interrompez votre activité professionnelle), 
#        vous ne pouvez pas bénéficier du Cmg.         
    clmg_brut = elig*not_(self.clca_taux_plein)*clmg_brut
    
    # TODO vérfiez les règles de cumul        
    
    self.clmg_brut = clmg_brut.sum(axis=0)
    
def pajeColca( _P):    
    '''
    Prestation d'accueil du jeune enfant - Complément optionnel de libre choix du mode de garde
    '''

    opt_colca = zeros((12,self.taille))
    P = _P.fam
    condition = (age_en_mois_benjamin(P,0) < 12*P.paje.colca.age )*(age_en_mois_benjamin(P,0) >=0)   
    nbenf = NbEnf(P.af.age1,P.af.age2)
    
    paje = (self.paje_brut_m > 0)  
    colca_brut = opt_colca*condition*(nbenf>=3)*P.af.bmaf*(
        (paje)*P.paje.colca.avecab + not_(paje)*P.paje.colca.sansab )

    return colca_brut.sum(axis=0)

    #TODO: cumul avec clca self.colca_tot_m 

def CumulPajeCf(self, _P):
    '''
    L'allocation de base de la paje n'est pas cummulable avec le complément familial
    '''
    P = _P.fam
    crds = P.af.crds
    
    # On regarde ce qui est le plus intéressant pour la famille, chaque mois
    paje_brut_m = (self.paje_brut_m >= self.cf_brut_m)*self.paje_brut_m
    cf_brut_m   = (self.paje_brut_m <  self.cf_brut_m)*self.cf_brut_m
    
    self.paje_brut  = round(paje_brut_m.sum(axis=0), 2)
    self.paje_crds  = round(self.paje_brut*crds, 2)
    self.paje_tot   = self.paje_brut - self.paje_crds
#        self.paje_tot_m = round(self.paje_brut_m*(1-crds), 2)

    table = self.population
    table.openWriteMode()
    table.set('paje', self.paje_tot, 'fam', 'chef', table = 'output')
    
    self.cf_brut = round(cf_brut_m.sum(axis=0), 2)
    self.cf_crds   = round(self.cf_brut*crds, 2)
    self.cf_tot    = self.cf_brut - self.cf_crds
#        self.cf_tot_m = round(self.cf_brut_m*(1-crds), 2)
    
    table.set('cf', self.cf_tot, 'fam', 'chef', table = 'output')
    table.close_()
    
@famille_wrapper(crds=False)
def AEEH(self, Param):
    '''
    Allocation d'éducation de l'enfant handicapé (Allocation d'éducation spécialisée avant le 1er janvier 2006)
    '''
#        
#        Ce montant peut être majoré par un complément accordé par la Cdaph qui prend en compte :
#        le coût du handicap de l'enfant,
#        la cessation ou la réduction d'activité professionnelle de l'un ou l'autre des deux parents,
#        l'embauche d'une tierce personne rémunérée.
#
#        Une majoration est versée au parent isolé bénéficiaire d'un complément d'Aeeh lorsqu'il cesse ou réduit son activité professionnelle ou lorsqu'il embauche une tierce personne rémunérée.
    P = Param.fam
    enfhand = np.array( [ getattr(self, 'inv%d' %(i+1)) for i in range(self.nbenfmax) ] )
    ages =  self.getAges()

    enfhand = (enfhand*(ages < P.aeeh.age)).sum(axis=0)/12
    
    isole =  isol
    categ = ones((self.nbenfmax,self.taille)) 
    
    if self.datesim <= date(2002, 1,1): 
        aeeh = 0*enfhand
    else:
        aeeh  = enfhand*(P.af.bmaf*(P.aeeh.base + 
                              P.aeeh.cpl1*(categ==1) + 
                              (categ==2)*(P.aeeh.cpl2 + P.aeeh.maj2*isole) + 
                              (categ==3)*(P.aeeh.cpl3 + P.aeeh.maj3*isole) + 
                              (categ==4)*(P.aeeh.cpl4 + P.aeeh.maj4*isole) + 
                              (categ==5)*(P.aeeh.cpl5 + P.aeeh.maj5*isole) +
                              (categ==6)*(P.aeeh.maj6*isole)) +
                              (categ==6)*P.aeeh.cpl6 )

# L'attribution de l'AEEH de base et de ses compléments éventuels ne fait pas obstacle au 
# versement des prestations familiales.
# L'allocation de présence parentale peut être cumulée avec l'AEEH de base, mais pas avec son 
# complément ni avec la majoration de parent isolé.
# Tous les éléments de la prestattion de compensation du handicap (PCH) sont également ouverts 
# aux bénéficiaires de l'AEEH de base, sous certaines conditions, mais ce cumul est exclusif du 
# complément de l'AEEH. Les parents d'enfants handicapés doivent donc choisir entre le versement 
# du complément d'AEEH et la PCH.   
            
    # Ces allocations ne sont pas soumis à la CRDS
    self.aeeh_brut  = 12*aeeh.sum(axis=0)  

def APE(self, Param):
    ''' 
    L’allocation parentale d’éducation s’adresse aux parents qui souhaitent arrêter ou 
    réduire leur activité pour s’occuper de leurs jeunes enfants, à condition que ceux-ci 
    soient nés avant le 01/01/2004. En effet, pour les enfants nés depuis cette date, 
    dans le cadre de la Prestation d’Accueil du Jeune Enfant, les parents peuvent bénéficier 
    du « complément de libre choix d’activité. »
    '''    
    
    # TODO cumul (hyper important), adoption, triplés, 
    # L'allocation parentale d'éducation n'est pas soumise 
    # à condition de ressources, sauf l’APE à taux partiel pour les professions non salariées
    P = Param.fam
    elig = (self.NbEnf(0,P.ape.age-1)>=1) & (self.NbEnf(0,P.af.age2)>=2)
    
    # TODO: rajouter ces infos aux parents
    inactif  = zeros((12,self.taille))
    # Temps partiel 1
    # Salarié: 
    # Temps de travail ne dépassant pas 50 % de la durée du travail fixée dans l'entreprise
    # VRP ou non salarié travaillant à temps partiel:
    # Temps de travail ne dépassant pas 76 heures par mois et un revenu professionnel mensuel inférieur ou égal à (smic_8.27*169*85 %)
    partiel1 = zeros((12,self.taille))
    
    # Temps partiel 2
    # Salarié:
    # Salarié: Temps de travail compris entre 50 et 80 % de la durée du travail fixée dans l'entreprise.
    # Temps de travail compris entre 77 et 122 heures par mois et un revenu professionnel mensuel ne dépassant pas
    #  (smic_8.27*169*136 %)

    partiel2  = zeros((12,self.taille))
    self.ape_brut_m = elig*(inactif*P.ape.tx_inactif + partiel1*P.ape.tx_50 + partiel2*P.ape.tx_80)
    

def APJE(self,Param):
    '''
    Allocation pour jeune enfant
    '''
    # TODO: APJE courte voir doc ERF 2006
    P = Param.fam
    nbenf = self.NbEnf(0,P.apje.age-1)
    bmaf = P.af.bmaf
    bmaf_n_2= P.af.bmaf_n_2 
    base = round(P.apje.taux*bmaf,2)
    base2 = round(P.apje.taux*bmaf_n_2,2)

    plaf_tx = (nbenf>0) + P.apje.plaf_tx1*min_(nbenf,2) + P.apje.plaf_tx2*max_(nbenf-2,0)
    majo    = isol | self.biact
    plaf    = P.apje.plaf*plaf_tx + P.apje.plaf_maj*majo
    plaf2   = plaf + 12*base2    

    brut =  (nbenf>=1)*( ( br_pf <= plaf)*base 
            + (br_pf > plaf)*max_(plaf2-br_pf,0)/12.0 )
    self.apje_brut_m = brut


def CumulAPE_APJE_CF(self, Param):
    P = Param.fam
    crds = P.af.crds
    apje_brut_m = (self.apje_brut_m > max_(self.cf_brut_m,self.ape_brut_m))*self.apje_brut_m
    cf_brut_m   = (self.cf_brut_m  >= max_(self.apje_brut_m,self.ape_brut_m) )*self.cf_brut_m
    ape_brut_m  = (self.ape_brut_m  > max_(self.apje_brut_m,self.cf_brut_m) )*self.ape_brut_m
            
    self.apje_brut  = round(apje_brut_m.sum(axis=0), 2)
    self.apje_crds  = round(self.apje_brut*crds, 2)
    self.apje_tot   = self.apje_brut - self.apje_crds

    self.cf_brut   = round(cf_brut_m.sum(axis=0), 2)
    self.cf_crds   = round(self.cf_brut*crds, 2)
    self.cf_tot    = self.cf_brut - self.cf_crds

    self.ape_brut  = round(ape_brut_m.sum(axis=0), 2)
    self.ape_crds  = round(self.ape_brut*crds, 2)
    self.ape_tot   = self.ape_brut - self.ape_crds
    
    table.openWriteMode()
    table.set('chef', 'apje', self.apje_tot, 'fam')
    table.set('chef', 'cf', self.cf_tot, 'fam')
    table.set('chef', 'ape', self.ape_tot, 'fam')    
    table.close_()
    
    
## TODO rajouter la prime à la naissance et à l'adoption avant la paje

@famille_wrapper()        
def AGED(self,Param):
    '''
    Allocation garde d'enfant à domicile
    '''
    # TODO: trimestrialiser 
    # les deux conjoints actif et revenu min requis
    # A complêter

    P = Param.fam
    ape_taux_partiel_dummy  = zeros(self.taille)
    
    nbenf = self.NbEnf(0, P.aged.age1-1)
    nbenf2 = self.NbEnf(0, P.aged.age2-1)

    elig1 = (nbenf>0) 
    elig2 = not_(elig1)*(nbenf2>0)*ape_taux_partiel_dummy
    
    depenses_trim = zeros(self.taille)   # TODO gérer les dépenses trimestrielles
    depenses = 4*depenses_trim         
             
    aged3 = elig1*( max_(P.aged.remb_plaf1-P.aged.remb_taux1*depenses,0)*(br_pf > P.aged.revenus_plaf) 
       +  (br_pf <= P.aged.revenus_plaf)*max_(P.aged.remb_taux2*depenses - P.aged.remb_plaf1,0))
    
    aged6  = elig2*max_(P.aged.remb_taux2*depenses - P.aged.remb_plaf2,0)

    self.aged = aged3 + aged6 

@famille_wrapper()        
def AFEAMA(self,Param):
    '''
    Aide à la famille pour l'emploi d'une assistante maternelle agréée
    '''
    # TODO http://web.archive.org/web/20080205163300/http://www.caf.fr/wps/portal/particuliers/catalogue/metropole/afeama
    
    # seuils sont de 80 et 110 % de l'ARS
    # Vérifier que c'est la même chose pour le clmg
    P = Param.fam
    ape = zeros(self.taille)
    elig = not_(ape)*zeros(self.taille) # assistante maternelle agréee
# Vous devez:
#    faire garder votre enfant de moins de 6 ans par une assistante maternelle agréée dont vous êtes l'employeur
#    déclarer son embauche à l'Urssaf
#    lui verser un salaire ne dépassant pas par jour de garde et par enfant 5 fois le montant horaire du Smic, soit au max_ 42,20 €
#
#Si vous cessez de travailler et bénéficiez de l'allocation parentale d'éducation, vous ne recevrez plus l'Afeama.
#Vos enfants doivent être nés avant le 1er janvier 2004.

    # TODO calcul des cotisations urssaf
    # 
    nbenf = elig*self.NbEnf(P.af.age1,P.age2)*(self.NbEnf(P.af.age1,P.afeama.age-1)>0)
    
    seuil1 = P.afeama.mult_seuil1*P.ars.plaf*(nbenf==1) + max_(nbenf-1,0)*P.afeama.mult_seuil1*P.ars.plaf*(1+P.ars.plaf_enf_supp)
    seuil2 = P.afeama.mult_seuil2*P.ars.plaf*(nbenf==1) + max_(nbenf-1,0)*P.afeama.mult_seuil2*P.ars.plaf*(1+P.ars.plaf_enf_supp)
    
    afeama_brut = self.NbEnf(P.af.age1,P.afeama.age-1)*P.af.bmaf*( 
            (br_pf < seuil1)*P.afeama.taux_mini +
            ( (br_pf >= seuil1) & (br_pf < seuil2) )*P.afeama.taux_median +
            (br_pf >= seuil2)*P.afeama.taux_maxi)
    
    self.afeama_brut_m = afeama_brut.sum(axis=0)

def AL(self, P):
    self.AlNbp(P)
    self.AlBaseRessource(P)
    self.AlFormule(P)

def AlNbp(self,P):
    '''
    Nombre de personne à charge au sens des allocations logement
    '''

    # site de la CAF en 2011: 
    ## Enfant à charge
    # Vous assurez financièrement l'entretien et asez la responsabilité 
    # affective et éducative d'un enfant, que vous ayez ou non un lien de 
    # parenté avec lui. Il est reconnu à votre charge pour le versement 
    # des aides au logement jusqu'au mois précédent ses 21 ans.
    # Attention, s'il travaille, il doit gagner moins de 836,55 € par mois.
    ## Parents âgés ou infirmes
    # Sont à votre charge s'ils vivent avec vous et si leurs revenus 2009 
    # ne dépassent pas 10 386,59 € :
    #   * vos parents ou grand-parents âgés de plus de 65 ans ou d'au moins
    #     60 ans, inaptes au travail, anciens déportés,
    #   * vos proches parents infirmes âgés de 22 ans ou plus (parents, 
    #     grand-parents, enfants, petits enfants, frères, soeurs, oncles, 
    #     tantes, neveux, nièces).
    # P_AL.D_enfch est une dummy qui vaut 1 si les enfants sont comptés à
    # charge (cas actuel) et zéro sinon.
    age1 = P.fam.af.age1
    age2 = P.fam.cf.age2
    al_nbenf = self.NbEnf(age1, age2)
    al_nbenf = al_nbenf[0,:]
    self.al_pac = P.al.autres.D_enfch*(al_nbenf + self.al_nbinv) # manque invalides
    # TODO: il faudrait probablement définir les AL pour un ménage et non 
    # pour une famille
    
def AlBaseRessource(self,P):
    '''
    Base ressource des allocations logement
    '''
    # On ne considère que les revenus des 2 conjoints et les revenus non
    # individualisable
    # self.etu_vs et self.etu_cj
    #   0 - non étudiant
    #   1 - étudiant non boursier
    #   2 - éutidant boursier
    # self.vous et self.conj : somme des revenus catégoriel après abatement
    # self.coll autres revenus du ménage non individualisable
    # self.ALabat abatement prix en compte pour le calcul de la base ressources
    # des allocattions logement
    # plancher de ressources pour les etudiants
    Pr = P.al.ressources
    
    
    etuC = (self.etuC>=1)&(self.etuP==0)
    etuP = (self.etuC==0)&(self.etuP>=1)
    etuCP= (self.etuC>=1)&(self.etuP>=1)
    self.etu = (self.etuC>=1)|(self.etuP>=1)
    
    revCatVous = max_(self.revChef,etuC*(Pr.dar_4-(self.etuC==2)*Pr.dar_5))
    revCatConj = max_(self.revPart,etuP*(Pr.dar_4-(self.etuP==2)*Pr.dar_5))
    revCatVsCj = not_(etuCP)*(revCatVous + revCatConj) + \
                    etuCP*max_(self.revChef + self.revPart, Pr.dar_4 -((self.etuC==2)|(self.etuP==2))*Pr.dar_5 + Pr.dar_7)
    
    # somme des revenus catégoriels après abatement
    revCat = revCatVsCj + self.revColl
    # charges déductibles : pension alimentaires et abatements spéciaux
    revNet = revCat
    
    # On ne considère pas l'abattement sur les ressources de certaines
    # personnes (enfant, ascendants ou grands infirmes).
    
    # abattement forfaitaire double activité
    abatDoubleAct = self.biact*Pr.dar_1 
    
    # neutralisation des ressources
    # ...
    
    # abbattement sur les ressources
    # ...
    
    # évaluation forfaitaire des ressources (première demande)
    
    # double résidence pour raisons professionnelles
    
    # Base ressource des aides au logement (arrondies aux 100 euros supérieurs)
    self.BRapl = ceil(max_(revNet - abatDoubleAct,0)/100)*100

def AlFormule(self,P):
    '''
    Formule des aides aux logements en secteur locatif
    Attention, cette fonction calcul l'aide mensuelle
    '''
    
    # ne prend pas en compte les chambres ni les logements-foyers.
    # variables nécéssaires dans FA
    # isol : ménage isolé
    # self.coup: ménage en coup (rq : self.coup = ~isol.
    # self.al_pac : nb de personne à charge du ménage prise en compte pour les AL
    # self.al_zone
    # self.loyer
    # self.BRapl : base ressource des al après abattement.
    # self.coloc (1 si colocation, 0 sinon)
    # self.SO : statut d'occupation du logement
    #   SO==1 : Accédant à la propriété
    #   SO==2 : Propriétaire (non accédant) du logement.
    #   SO==3 : Locataire d'un logement HLM
    #   SO==4 : Locataire ou sous-locataire d'un logement loué vie non-HLM
    #   SO==5 : Locataire ou sous-locataire d'un logement loué meublé ou d'une chambre d'hôtel.
    #   sO==6 : Logé gratuitement par des parents, des amis ou l'employeur
        
    loca = (3 <= self.so)&(5 >= self.so)
    acce = self.so==1
    rmi = P.al.rmi
    bmaf = P.fam.af.bmaf_n_2
        
    ## aides au logement pour les locataires
    # loyer;
    L1 = self.loyer
    # loyer plafond;
    lp_taux = (self.coloc==0)*1 + self.coloc*P.al.loyers_plafond.colocation
    
    z1 = P.al.loyers_plafond.zone1
    z2 = P.al.loyers_plafond.zone2
    z3 = P.al.loyers_plafond.zone3
    
    Lz1 = ((self.isol)*(self.al_pac==0)*z1.L1 + (self.coup)*(self.al_pac==0)*z1.L2 + (self.al_pac>0)*z1.L3 + (self.al_pac>1)*(self.al_pac-1)*z1.L4)*lp_taux
    Lz2 = ((self.isol)*(self.al_pac==0)*z2.L1 + (self.coup)*(self.al_pac==0)*z2.L2 + (self.al_pac>0)*z2.L3 + (self.al_pac>1)*(self.al_pac-1)*z2.L4)*lp_taux
    Lz3 = ((self.isol)*(self.al_pac==0)*z3.L1 + (self.coup)*(self.al_pac==0)*z3.L2 + (self.al_pac>0)*z3.L3 + (self.al_pac>1)*(self.al_pac-1)*z3.L4)*lp_taux
    
    L2 = Lz1*(self.al_zone==1) + Lz2*(self.al_zone==2) + Lz3*(self.al_zone==3)
    # loyer retenu
    L = min_(L1,L2)
    
    # forfait de charges
    P_fc = P.al.forfait_charges
    C = not_(self.coloc)*(P_fc.fc1 + self.al_pac*P_fc.fc2) + \
          ( self.coloc)*((self.isol*0.5 + self.coup)*P_fc.fc1 + self.al_pac*P_fc.fc2)
    
    # dépense éligible
    E = L + C;
    
    # ressources prises en compte 
    R = self.BRapl
    
    # Plafond RO    
    R1 = P.al.R1.taux1*rmi*(self.isol)*(self.al_pac==0) + \
         P.al.R1.taux2*rmi*(self.coup)*(self.al_pac==0) + \
         P.al.R1.taux3*rmi*(self.al_pac==1) + \
         P.al.R1.taux4*rmi*(self.al_pac>=2) + \
         P.al.R1.taux5*rmi*(self.al_pac>2)*(self.al_pac-2)
    
    R2 = P.al.R2.taux4*bmaf*(self.al_pac>=2) + \
         P.al.R2.taux5*bmaf*(self.al_pac>2)*(self.al_pac-2)
    
    Ro = round(12*(R1-R2)*(1-P.al.autres.abat_sal));
    
    Rp = max_(0, R - Ro );
    
    # Participation personnelle
    Po = max_(P.al.pp.taux*E, P.al.pp.min);
    
    # Taux de famille    
    TF = P.al.TF.taux1*(self.isol)*(self.al_pac==0) + \
         P.al.TF.taux2*(self.coup)*(self.al_pac==0) + \
         P.al.TF.taux3*(self.al_pac==1) + \
         P.al.TF.taux4*(self.al_pac==2) + \
         P.al.TF.taux5*(self.al_pac==3) + \
         P.al.TF.taux6*(self.al_pac>=4) + \
         P.al.TF.taux7*(self.al_pac>4)*(self.al_pac-4)
    
    # Loyer de référence
    L_Ref = z2.L1*(self.isol)*(self.al_pac==0) + \
            z2.L2*(self.coup)*(self.al_pac==0) + \
            z2.L3*(self.al_pac>=1) + \
            z2.L4*(self.al_pac>1)*(self.al_pac-1)

    RL = L / L_Ref

    # TODO ; paramètres en dur ??
    TL = max_(max_(0,P.al.TL.taux2*(RL-0.45)),P.al.TL.taux3*(RL-0.75)+P.al.TL.taux2*(0.75-0.45))
    
    Tp= TF + TL
    
    PP = Po + Tp*Rp
    al_loc = max_(0,E - PP)*(loca==1)
    self.al_loc = al_loc*(al_loc>=P.al.autres.nv_seuil)

    ## APL pour les accédants à la propriété
    self.al_acc = zeros(self.taille)*(acce==1)

    ## APL (tous)
    self.al_tot = (self.al_loc + self.al_acc)*(1-P.fam.af.crds)

    self.alf   = 12*(self.al_pac>=1)*self.al_tot # Allocation logement familiale
    self.als   = 12*(self.al_pac==0)*not_(self.etu)*self.al_tot # Allocation logement sociale
    self.alset = 12*(self.al_pac==0)*self.etu*self.al_tot # Allocation logement étudiante
    self.apl   = 12*zeros(self.taille) #TODO: Pour les logements conventionné (surtout des HLM)

    table = self.population
    table.openWriteMode()
    table.set('alf', self.alf, 'fam', 'chef', table = 'output')
    table.set('als', self.als, 'fam', 'chef', table = 'output')
    table.set('alset', self.alset, 'fam', 'chef', table = 'output')
    table.set('apl', self.apl, 'fam', 'chef', table = 'output')
    table.close_()

def BaseRessourceMV(self, P):
    '''
    Base ressource du minimlum vieillesse et assimilé (ASPA)
    '''    
    #Ressources prises en compte
    #Tous les avantages de vieillesse et d'invalidité dont bénéficie l'intéressé sont pris en compte dans l'appréciation des ressources, de même que les revenus professionnels, les revenus des biens mobiliers et immobiliers et les biens dont il a fait donation dans les 10 années qui précèdent la demande d'Aspa.
    #L'évaluation des ressources d'un couple est effectuée de la même manière, sans faire la distinction entre les biens propres ou les biens communs des conjoints, concubins ou partenaires liés par un Pacs.
    #Ressources exclues
    #Certaines ressources ne sont toutefois pas prises en compte dans l'estimation des ressources. Il s'agit notamment :
    #de la valeur des locaux d'habitation occupés par le demandeur et les membres de sa famille vivant à son foyer lorsqu'il s'agit de sa résidence principale,
    # des prestations familiales,
    # de l'allocation de logement sociale,
    # des majorations prévues par la législation, accordées aux personnes dont l'état de santé nécessite l'aide constante d'une tierce personne,
    # de la retraite du combattant,
    # des pensions attachées aux distinctions honorifiques,
    # de l'aide apportée ou susceptible d'être apportée par les personnes tenues à l'obligation alimentaire.

    self.BRmv = (max_(0,self.sal + self.cho) + max_(0,self.rst + self.alr + self.rto) + 
                 max_(0,self.rpns) + max_(0,self.revcap_bar) + 
                 max_(0,self.revcap_lib) + max_(0,self.rfon) +
                 max_(0,self.etr) + max_(0,self.div_rmi) )
    return self.BRmv

def MV(self, Param):
    '''
    Minimum vieillesse - Allocation de solidarité aux personnes agées (ASPA)
    '''
    # age minimum (CSS R815-2)
    # base ressource R815-25: 
    #   - retraite, pensions et rentes,
    #   - allocation spéciale (L814-1);
    #   - allocation aux mères de famille (L813)
    #   - majorations pour conjoint à charge des retraites
    #   - pas de prise en compte des allocations logement, des prestations
    #   familiales, de la rente viagère rapatriée...
    # majoration si le conjoint à lui aussi plus de 65 ans, ou 60 si inapte;
    # TODO: ajouter taux de la majoration pour 3 enfants 10% (D811-12) ?
    #       P.aspa.maj_3enf = 0.10;
    P = Param.minim

    
    ageC = np.floor(np.array([m + self.agemC for m in range(12)])/12)
    ageP = np.floor(np.array([m + self.agemP for m in range(12)])/12)

    eligC = ((ageC>=P.aspa.age_min) | ((ageC>=P.aspa.age_ina) &  (self.invC==1))) & (self.actC==3) 
    eligP = ((ageP>=P.aspa.age_min) | ((ageP>=P.aspa.age_ina) &  (self.invP==1))) & (self.actP==3)
    
    elig2 = eligC & eligP
    elig1 = not_(elig2) & (eligC |eligP)
    
    BRmv = self.BaseRessourceMV(P)
    
    depassement = elig1*(self.nbpar==1)*max_(0, BRmv + P.aspa.montant_seul - P.aspa.plaf_seul )/12 \
        +  elig1*(self.nbpar==2)*max_(0, BRmv + P.aspa.montant_seul - P.aspa.plaf_couple )/12 \
        +  elig2*max_(0, BRmv + P.aspa.montant_couple - P.aspa.plaf_couple )/12
    
    self.mv_m = max_(0,elig1*P.aspa.montant_seul + elig2*P.aspa.montant_couple -  depassement) 

    # TODO ASI 
    self.asiC = zeros(self.taille)
    self.asiP = zeros(self.taille)

    self.mv = self.mv_m.sum(axis=0)

    
    table.openWriteMode()
    table.set('chef', 'mv', self.mv, 'fam')
    table.close_()

def RSA(self, P):
    self.RmiNbp(P.minim)
    self.RmiBaseRessource(P.minim)
    self.Rsa(P.minim)
    self.API(P) 

def RMI(self, P):
    self.RmiNbp(P.minim)
    self.RmiBaseRessource(P.minim)
    self.Rsa(P.minim)

def RmiNbp(self,P):
    '''
    Nombre de personne à charge au sens du Rmi ou du Rsa
    '''
    self.rmiNbp = self.nbpar + self.NbEnf(0,24)[0,:]

def RmiBaseRessource(self, P):
    # compléter la base ressource RMI
    
    # base ressource du rmi, on prend en compte tous les revenus, sans
    # abattement;
    # 
    # 1 L’ensemble des revenus tirés d’une activité salariée ou non salariée ;
    # 2 Les revenus tirés de stages de formation professionnelle ;
    # 3 Les revenus tirés de stages réalisés en application de l’article 9 de 
    #   la loi no  2006-396 du 31 mars 2006 pour l’égalité des chances ;
    # 4 L’aide légale ou conventionnelle aux salariés en chômage partiel ;
    # 5 Les indemnités perçues à l’occasion des congés légaux de maternité, de paternité ou d’adoption ;
    # 6 Les indemnités journalières de sécurité sociale, de base et complémentaires, perçues en cas d’incapacité
    #   physique médicalement constatée de continuer ou de reprendre le travail, d’accident du travail ou de maladie
    #   professionnelle pendant une durée qui ne peut excéder trois mois à compter de l’arrêt de travail

    # RaRsa revenus d'activité au sens du RSA

    if self.datesim < date(2004, 1,1):
        pfBRrmi =  P.rmi.pfInBRrmi*(self.af_base + self.cf_tot + self.asf_brut + 
                                    self.apje_tot + self.ape_tot)    
    else: 
        pfBRrmi =  P.rmi.pfInBRrmi*(self.af_base + self.cf_tot + self.asf_brut + 
                                    self.paje_tot + self.clca_brut + self.colca_brut)


    self.BrRmi = (self.RaRsaC + self.RaRsaP + self.cho + self.rst + self.alr + self.rto + 
                  max_(0,self.revcap_bar + self.revcap_lib + self.rfon) + 
                  pfBRrmi +
                  self.mv + self.asiC + self.asiP + self.aah + self.caah)
      

    # Ne sont pas pris en compte:
    #  
    # 1 De la prime à la naissance ou à l’adoption mentionnée à l’article L. 531-2 du code de la sécurité
    #   sociale ;
    # 2 De l’allocation de base mentionnée à l’article L. 531-3 du code de la sécurité sociale due pour le mois
    #   au cours duquel intervient la naissance ou, dans les situations visées à l’article L. 262-9 du présent code,
    #   jusqu’au dernier jour du mois civil au cours duquel l’enfant atteint l’âge de trois mois ;
    # 3 De la majoration pour âge des allocations familiales mentionnée à l’article L. 521-3 du code de la
    #   sécurité sociale ainsi que de l’allocation forfaitaire instituée par le second alinéa de l’article L. 521-1 du même
    #   code ;
    # 4 De l’allocation de rentrée scolaire mentionnée à l’article L. 543-1 du code de la sécurité sociale ;
    # 5 Du complément de libre choix du mode de garde mentionné aux articles L. 531-5 à L. 531-9 du code de
    #   la sécurité sociale ;16 avril 2009 JOURNAL OFFICIEL DE LA RÉPUBLIQUE
    #   FRANÇAISE Texte 3 sur 110. 
    # 6 De l’allocation d’éducation de l’enfant handicapé et de ses compléments mentionnés à l’article L. 541-1
    #   du code de la sécurité sociale, de la majoration spécifique pour personne isolée mentionnée à l’article L. 541-4
    #   du même code ainsi que de la prestation de compensation du handicap lorsqu’elle est perçue en application de
    #   l’article 94 de la loi no 2007-1786 du 19 décembre 2007 de financement de la sécurité sociale pour 2008 ;
    # 7 De l’allocation journalière de présence parentale mentionnée à l’article L. 544-1 du code de la sécurité sociale ;
    # 8 Des primes de déménagement prévues par les articles L. 542-8 du code de la sécurité sociale et L. 351-5
    #   du code de la construction et de l’habitation ;
    # 9 De la prestation de compensation mentionnée à l’article L. 245-1 ou de l’allocation compensatrice
    #   prévue au chapitre V du titre IV du livre II du code de l’action sociale et des familles dans sa rédaction antérieure 
    #   à la loi no 2005-102 du 11 février 2005 pour l’égalité des droits et des chances, la participation et la
    #   citoyenneté des personnes handicapées, lorsque l’une ou l’autre sert à rémunérer un tiers ne faisant pas partie
    #   du foyer du bénéficiaire du revenu de solidarité active ;
    #10 Des prestations en nature dues au titre des assurances maladie, maternité, accidents du travail et
    #   maladies professionnelles ou au titre de l’aide médicale de l’Etat ;
    #11 De l’allocation de remplacement pour maternité prévue par les articles L. 613-19-1 et L. 722-8-1 du
    #   code de la sécurité sociale et L. 732-10 du code rural ;
    #12 De l’indemnité en capital attribuée à la victime d’un accident du travail prévue à l’article L. 434-1 du
    #   code de la sécurité sociale ;
    #13 De la prime de rééducation et du prêt d’honneur mentionnés à l’article R. 432-10 du code de la sécurité
    #   sociale ;
    #14 Des aides et secours financiers dont le montant ou la périodicité n’ont pas de caractère régulier ainsi
    #   que des aides et secours affectés à des dépenses concourant à l’insertion du bénéficiaire et de sa famille,
    #   notamment dans les domaines du logement, des transports, de l’éducation et de la formation ;
    #15 De la prime de retour à l’emploi et de l’aide personnalisée de retour à l’emploi mentionnées
    #   respectivement aux articles L. 5133-1 et L. 5133-8 du code du travail ainsi que de l’allocation mentionnée à
    #   l’article L. 5131-6 du même code ;
    #16 Des bourses d’études ainsi que de l’allocation pour la diversité dans la fonction publique ;
    #17 Des frais funéraires mentionnés à l’article L. 435-1 du code de la sécurité sociale ;
    #18 Du capital décès servi par un régime de sécurité sociale ;
    #19 De l’allocation du fonds de solidarité en faveur des anciens combattants d’Afrique du Nord prévue à
    #   l’article 125 de la loi no 91-1322 de finances pour 1992 ;
    #20 De l’aide spécifique en faveur des conjoints survivants de nationalité française des membres des
    #   formations supplétives et assimilés, mentionnée aux premier et troisième alinéas de l’article 10 de la loi
    #   no 94-488 du 11 juin 1994 relative aux rapatriés, anciens membres des formations supplétives et assimilés ou
    #   victimes de la captivité en Algérie ;
    #21 De l’allocation de reconnaissance instituée par l’article 47 de la loi no 99-1173 de finances rectificative pour 1999 ;
    #22 Des mesures de réparation mentionnées à l’article 2 du décret no 2000-657 du 13 juillet 2000 instituant
    #   une mesure de réparation pour les orphelins dont les parents ont été victimes de persécutions antisémites ;
    #23 Des mesures de réparation mentionnées à l’article 2 du décret no 2004-751 du 27 juillet 2004 instituant
    #   une aide financière en reconnaissance des souffrances endurées par les orphelins dont les parents ont été
    #   victimes d’actes de barbarie durant la Deuxième Guerre mondiale


def Rsa(self, P):
    table = self.population
    # RSA socle TODO mécanisme similaire à l'API: Pour les
    # personnes ayant la charge d’au moins un enfant né ou à
    # naître et se retrouvant en situation d’isolement, le montant
    # forfaitaire est majoré pendant 12 mois, continus ou non,
    # dans la limite de 18 mois à compter de la date du fait
    # générateur de l’isolement. Le cas échéant, la durée de
    # majoration est prolongée jusqu’à ce que le plus jeune enfant
    # atteigne trois ans.        
    loca = (3 <= self.so)&(5 >= self.so)
    eligib = (self.ageC>=25) |(self.ageP>=25)
    tx_rmi = 1 + ( self.rmiNbp >= 2 )*P.rmi.txp2 \
               + ( self.rmiNbp >= 3 )*P.rmi.txp3 \
               + ( self.rmiNbp >= 4 )*((self.nbpar==1)*P.rmi.txps + (self.nbpar!=1)*P.rmi.txp3) \
               + max_(self.rmiNbp -4,0)*P.rmi.txps 
    rsaSocle = 12*P.rmi.rmi*tx_rmi*eligib
    # calcul du forfait logement si le ménage touche des allocations logements
    # (FA.AL)
    FL = P.rmi.forfait_logement
    tx_fl = ((self.rmiNbp==1)*FL.taux1 +
             (self.rmiNbp==2)*FL.taux2 +
             (self.rmiNbp>=3)*FL.taux3 )
    self.forf_log = 12*loca*(tx_fl*P.rmi.rmi)
    # cacul du RSA
    RMI = max_(0,rsaSocle  - self.forf_log - self.BrRmi)
    RSA = max_(0,rsaSocle + P.rmi.pente*(self.RaRsaC+self.RaRsaP) - self.forf_log - self.BrRmi)
    self.rsa = (RSA>=P.rmi.rsa_nv)*RSA
    
    table.openWriteMode()        
    table.set('rsaact', self.rsa - RMI, 'fam', 'chef', table = 'output')
    table.set('rsa'   , self.rsa,       'fam', 'chef', table = 'output')   
    table.close_()
    
    table.openReadMode()        
    # On retranche le RSA activité de la PPE
    ppe = max_(table.get('ppe', 'foy', 'vous', table = 'output') 
           - table.get('rsaact', 'foy', 'vous', table = 'output')
           - table.get('rsaact', 'foy', 'conj', table = 'output'),0)
    table.close_()
    
    table.openWriteMode()
    table.setColl('ppe',ppe, table = 'output')
    table.close_()    

def API(self, P):
    '''
    Allocation de parent isolé
    '''
    if self.nbenfmax == 0:
        self.api = zeros(self.taille)
        return

    bmaf = P.fam.af.bmaf;
    benjamin = self.age_en_mois_benjamin(P.fam, 9)
    enceinte = (benjamin<0)*(benjamin>-6)
    # TODO quel mois mettre ?
    # TODO pas complètement exact
    # L'allocataire perçoit l'API :
    # jusqu'à ce que le plus jeune enfant ait 3 ans,
    # ou pendant 12 mois consécutifs si les enfants sont âgés de plus de 3 ans 
    #    et s'il a présenté sa demande dans les 6 mois à partir du moment où il 
    #    assure seul la charge de l'enfant. 
    # TODO: API courte gens pour les gens qui ont divorcés dans l'année
    # Le droit à l'allocation est réétudié tous les 3 mois.
    ## Calcul de l'année et mois de naissance du benjamin 
    
    condition = (np.floor(benjamin/12) <= P.minim.api.age-1)
    eligib = self.isol*( (enceinte!=0) | (self.NbEnf(0,P.minim.api.age-1)>0) )*condition;

    # moins de 20 ans avant inclusion dans rsa et moins de  25 après
    api1 = eligib*bmaf*(P.minim.api.base + P.minim.api.enf_sup*self.NbEnf(P.fam.af.age1,P.minim.api.age_pac-1) )
    rsa = (P.minim.api.age_pac >= 25) # dummy passage au rsa majoré
    BRapi = self.BrRmi + self.af_majo*not_(rsa)
    # TODO: mensualiser RMI, BRrmi et forfait logement
    api  = max_(0, api1 - self.forf_log/12 - BRapi/12 - self.rsa/12) 
    
    # L'API est exonérée de CRDS
    self.api = api.sum(axis=0)
    table = self.population
    table.openWriteMode()
    table.set('api', self.api, 'fam', 'chef', table = 'output')
    table.close_()

    # TODO: temps partiel qui modifie la base ressource
    # Cumul
    # Cumul avec un revenu
    # Si l'allocataire reprend une activité ou suit une formation professionnelle rémunérée, les revenus sont cumulables intégralement au cours des 3 premiers mois de reprise d'activité.
    # Du 4e au 12e mois qui suit, le montant de l'allocation varie en fonction de la durée de l'activité ou de la formation.
    # Durée d'activité de 78 heures ou plus par mois ou activité non salariée
    # Lorsque la durée d'activité est de 78 heures minimum par mois, le montant de l'API perçu par l'allocataire est diminué de la totalité du salaire. Tous les revenus d'activité sont pris en compte pour le calcul de l'API, sauf si l'allocataire perçoit des revenus issus d'un contrat insertion-revenu minimum d'activité (CIRMA) ou d'un contrat d'avenir (CAV).
    # L'allocataire peut bénéficier, sous certaines conditions :
    # • de la prime de retour à l'emploi si son activité est d'une durée d'au moins 4 mois consécutifs, sauf s'il effectue un stage de formation professionnelle,
    # • de la prime forfaitaire pendant 9 mois, sauf s'il exerce une activité salariée dans le cadre d'un CIRMA ou d'un CAV.
    # Durée d'activité de moins de 78 heures par mois
    # Lorsque la durée d'activité est inférieure à 78 heures par mois, le montant de l'API perçu par l'allocataire est diminué de la moitié du salaire.
    # Si l'allocataire exerce une activité dans le cadre d'un CIRMA ou d'un CAV, ses revenus d'activité ne sont pas pris en compte pour le calcul de son API.

def AEFA(self, Param):
    '''
    Aide exceptionelle de fin d'année (prime de Noël)
    '''
        # Insituée en 1998        
        # Complément de rmi dans les ERF
    
    P = Param
    ass = zeros(self.taille)
    aer = zeros(self.taille)
    api = zeros(self.taille)
    rmi = self.rsa>0

    # Le montant de l’aide mentionnée à l’article 1er versée aux bénéficiaires de l’allocation de solidarité
    # spécifique à taux majoré servie aux allocataires âgés de cinquante-cinq ans ou plus justifiant de vingt années
    # d’activité salariée, aux allocataires âgés de cinquante-sept ans et demi ou plus justifiant de dix années d’activité
    # salariée ainsi qu’aux allocataires justifiant d’au moins 160 trimestres validés dans les régimes d’assurance
    # vieillesse ou de périodes reconnues équivalentes est égal à        
    maj = zeros(self.taille)  # TODO
    
    condition = ass*aer*api*rmi
    
    if hasattr(P.fam.af,"age3"): nbPAC = self.NbEnf(P.fam.af.age1,P.fam.af.age3)[11,:]
    else: nbPAC = self.NbEnf(P.fam.af.age1,P.fam.af.age2)[11,:]
    # TODO check nombre de PAC pour une famille
    P = Param.minim
    aefa = condition*P.aefa.mon_seul*(1 + (self.nbpar==2)*P.aefa.tx_2p
              + nbPAC*P.aefa.tx_supp*(self.nbpar<=2)
              + nbPAC*P.aefa.tx_3pac*max_(nbPAC-2,0))
    
    if self.datesim.year==2008: aefa += condition*P.aefa.forf2008
               
    aefa_maj  = P.aefa.mon_seul*maj
    self.aefa = max_(aefa_maj,aefa)   
    
    self.population.openWriteMode()
    self.population.set('aefa', self.aefa, 'fam', 'chef', table = 'output')   
    self.population.close_()

def ASPA_ASI(self,Param):
    """
    Allocation de solidarité aux personnes agées (ASPA)
    et Allocation supplémentaire d'invalidité (ASI)
    """
    # ASPA crée le 1er janvier 2006
    # TODO Allocation supplémentaire avant le 1er janvier 2006
    
    # Anciennes allocations du minimum vieillesse remplacées par l'ASPA
    #
    #Il s'agit de :
    #    l'allocation aux vieux travailleurs salariés (AVTS),
    #    l'allocation aux vieux travailleurs non salariés,
    #    l'allocation aux mères de familles,
    #    l'allocation spéciale de vieillesse,
    #    l'allocation supplémentaire de vieillesse,
    #    l'allocation de vieillesse agricole,
    #    le secours viager,
    #    la majoration versée pour porter le montant d'une pension de vieillesse au niveau de l'AVTS,
    #    l'allocation viagère aux rapatriés âgés.

    
#        L'ASI peut être attribuée aux personnes atteintes d'une invalidité générale 
#        réduisant au moins des deux tiers leur capacité de travail ou de gain.
#        Les personnes qui ont été reconnues atteintes d'une invalidité générale réduisant 
#        au moins des deux tiers leur capacité de travail ou de gain pour l'attribution d'un 
#        avantage d'invalidité au titre d'un régime de sécurité sociale résultant de
#        dispositions législatives ou réglementaires sont considérées comme invalides.
    
#        Le droit à l'ASI prend fin dès lors que le titulaire remplit la condition d'âge pour bénéficier de l'ASPA.
#        Le titulaire de l'ASI est présumé inapte au travail pour l'attribution de l'ASPA. (cf. par analogie circulaire n° 70 SS du 05/08/1957 - circulaire Cnav 28/85 du 26/02/1985 - Lettre Cnav du 15.04.1986)
#        Le droit à l'ASI prend donc fin au soixantième anniversaire du titulaire. En pratique, l'allocation est supprimée au premier
#        jour du mois civil suivant le 60ème anniversaire.
    
#        Plafond de ressources communs depuis le 1er janvier 2006 
#        Changement au 1er janvier 2009 seulement pour les personnes seules !       
#        P.aspa.plaf_couple = P.asi.plaf_couple mais P.aspa.plaf_seul = P.asi.plaf_seul 
    
    # TODO à mensualiser 
    P = Param.minim        

    ageC = np.floor(np.array([m + self.agemC for m in range(12)])/12)
    ageP = np.floor(np.array([m + self.agemP for m in range(12)])/12)

    elig_aspa_C = ((ageC>=P.aspa.age_min) | ((ageC>=P.aspa.age_ina) &  (self.invC==1))) & (self.actC==3) 
    elig_aspa_P = ((ageP>=P.aspa.age_min) | ((ageP>=P.aspa.age_ina) &  (self.invP==1))) & (self.actP==3)
    
    elig_asi_C  = ( ((self.invC == 1) & (self.actC==3)) & not_(elig_aspa_C) ) 
    elig_asi_P  = ( ((self.invP == 1) & (self.actP==3)) & not_(elig_aspa_P) )  

    marpacs = self.coup
    maries  = self.maries
    
    # initialisation
    self.asiC_m  = zeros((12,self.taille))
    self.asiP_m  = zeros((12,self.taille))
    self.aspaC_m = zeros((12,self.taille))
    self.aspaP_m = zeros((12,self.taille))
    
    
    nb_alloc = (1*elig_aspa_C + 
                1*elig_aspa_P + 
                1*elig_asi_C + 
                1*elig_asi_P )   

    # 1 A Un ou deux bénéficiaire(s) de l'ASI et aucun bénéficiaire de l'ASPA 
    elig1 = ( (nb_alloc==1) & ( elig_asi_C | elig_asi_P) )      # un seul éligible
    elig2 = (elig_asi_C & elig_asi_P)*maries                    # couple d'éligible marié
    elig3 = (elig_asi_C & elig_asi_P)*(marpacs & not_(maries))  # couple d'éligible non marié
    elig  = elig1 | elig2

    montant_max = elig1*P.asi.montant_seul + elig2*P.asi.montant_couple + elig3*2*P.asi.montant_seul 
    ressources  = elig*(self.BaseRessourceMV(P) + montant_max)
    plafond_ressources = elig1*(P.asi.plaf_seul*not_(marpacs) + P.aspa.plaf_couple*marpacs) + elig2*P.aspa.plaf_couple + elig3*P.asi.plaf_couple
    depassement     = ressources - plafond_ressources 
    montant_servi   = max_(montant_max - depassement, 0)/12 
    self.asiC_m = elig_asi_C*montant_servi*(elig1*1 + elig2/2 + elig3/2)
    self.asiP_m = elig_asi_P*montant_servi*(elig1*1 + elig2/2 + elig3/2)

    # 1 B Un ou deux bénéficiaire de l'ASPA et aucun bénéficiaire de l'ASI
    elig1 = ( (nb_alloc==1) & ( elig_aspa_C | elig_aspa_P) )
    elig2 = (elig_aspa_C & elig_aspa_P)*maries
    elig  = elig1 | elig2

    montant_max = elig1*P.aspa.montant_seul + elig2*P.aspa.montant_couple
    ressources  = elig*(self.BaseRessourceMV(P) + montant_max) 
    plafond_ressources = elig1*(P.aspa.plaf_seul*not_(marpacs) + P.aspa.plaf_couple*marpacs) + elig2*P.aspa.plaf_couple
    depassement     = ressources - plafond_ressources 
    montant_servi   = max_(montant_max - depassement, 0)/12
    self.aspaC_m = elig_aspa_C*montant_servi*(elig1 + elig2/2)
    self.aspaP_m = elig_aspa_P*montant_servi*(elig1 + elig2/2)
            
    # 2 B Une personne peçoit l'ASI et l'autre l'ASPA
    # Les persones sont mariées 
    index = ( (elig_asi_C & elig_aspa_P) | (elig_asi_P & elig_aspa_C) )*(maries)
    montant_max = where( index, .5*P.asi.montant_couple + .5*P.aspa.montant_couple, 0)
    ressources  = where( index,self.BaseRessourceMV(P) + montant_max,0) 
    plafond_ressources = where( index, P.aspa.plaf_couple, 0)  
    depassement        = ressources - plafond_ressources 
    montant_servi_ASI   = where(index, max_(.5*P.asi.montant_couple  - 0.5*depassement, 0),0)/12
    montant_servi_ASPA  = where(index, max_(.5*P.aspa.montant_couple - 0.5*depassement, 0),0)/12
    self.asiC_m[index & elig_asi_C]  = montant_servi_ASI[index]
    self.asiP_m[index & elig_asi_P ] = montant_servi_ASI[index]
    self.aspaC_m[index & elig_aspa_C]  = montant_servi_ASPA[index]
    self.aspaP_m[index & elig_aspa_P ] = montant_servi_ASPA[index]
    
    # Les deux persones ne sont pas mariées mais concubins ou pacsés
    index = ( (elig_asi_C & elig_aspa_P) | (elig_asi_P & elig_aspa_C) )*(marpacs & not_(maries))
    montant_max = where( index, P.asi.montant_seul + .5*P.aspa.montant_couple , 0)
    ressources  = where( index,self.BaseRessourceMV(P) + montant_max,0) 
    plafond_ressources = where( index, P.aspa.plaf_couple, 0)  
    depassement        = ressources - plafond_ressources 
    montant_servi_ASI   = where(index, max_(P.asi.montant_seul - 0.5*depassement, 0),0)/12
    montant_servi_ASPA  = where(index, max_(.5*P.aspa.montant_couple - 0.5*depassement, 0),0)/12
    self.asiC_m[index & elig_asi_C]  = montant_servi_ASI[index]
    self.asiP_m[index & elig_asi_P ] = montant_servi_ASI[index]
    self.aspaC_m[index & elig_aspa_C]  = montant_servi_ASPA[index]
    self.aspaP_m[index & elig_aspa_P ] = montant_servi_ASPA[index]

    self.asiC  = self.asiC_m.sum(axis=0)
    self.asiP  = self.asiP_m.sum(axis=0)
    self.aspaC = self.aspaC_m.sum(axis=0)
    self.aspaP = self.aspaP_m.sum(axis=0)
    
    table = self.population
    table.openWriteMode()
    table.set('asi', self.asiC, 'fam', 'chef', table = 'output')
    table.set('asi', self.asiP, 'fam', 'part', table = 'output')
    table.set('mv', self.aspaC, 'fam', 'chef', table = 'output')
    table.set('mv', self.aspaP, 'fam', 'part', table = 'output')
    table.close_()
        
    self.mv = self.aspaC + self.aspaP    


def AAH(self, P):
    '''
    Allocation adulte handicapé (montant mensuel)
    '''
#        Conditions liées au handicap
#        La personne doit être atteinte d’un taux d’incapacité permanente :
#        - d’au moins 80 %,
#        - ou compris entre 50 et 79 %. Dans ce cas, elle doit remplir deux conditions 
#        supplémentaires : être dans l’impossibilité de se procurer un emploi compte 
#        tenu de son handicap et ne pas avoir travaillé depuis au moins 1 an
#        Condition de résidence
#        L'AAH peut être versée aux personnes résidant en France métropolitaine ou 
#         dans les départements d'outre-mer ou à Saint-Pierre et Miquelon de façon permanente. 
#         Les personnes de nationalité étrangère doivent être en possession d'un titre de séjour 
#         régulier ou être titulaire d'un récépissé de renouvellement de titre de séjour.
#        Condition d'âge
#        Age minimum : Le demandeur ne doit plus avoir l'âge de bénéficier de l'allocation d'éducation de l'enfant handicapé, c'est-à-dire qu'il doit être âgé :
#        - de plus de vingt ans,
#        - ou de plus de seize ans, s'il ne remplit plus les conditions pour ouvrir droit aux allocations familiales.
#        TODO: éligibilité AAH
#        Pour les montants http://www.handipole.org/spip.php?article666
    
#        Âge max_
#        Le versement de l'AAH prend fin à partir de l'âge minimum légal de départ à la retraite en cas d'incapacité 
#        de 50 % à 79 %. À cet âge, le bénéficiaire bascule dans le régime de retraite pour inaptitude.
#        En cas d'incapacité d'au moins 80 %, une AAH différentielle (c'est-à-dire une allocation mensuelle réduite) 
#        peut être versée au-delà de l'âge minimum légal de départ à la retraite en complément d'une retraite inférieure au minimum vieillesse.
    
#        N'entrent pas en compte dans les ressources :
#        L'allocation compensatrice tierce personne, les allocations familiales, 
#        l'allocation de logement, la retraite du combattant, les rentes viagères
#        constituées en faveur d'une personne handicapée ou dans la limite d'un 
#        montant fixé à l'article D.821-6 du code de la sécurité sociale (1 830 €/an),
#        lorsqu'elles ont été constituées par une personne handicapée pour elle-même. 
#        Le RMI (article R 531-10 du code de la sécurité sociale).
#        A partir du 1er juillet 2007, votre Caf, pour le calcul de votre Aah, 
#        continue à prendre en compte les ressources de votre foyer diminuées de 20%.
#        Notez, dans certaines situations, la Caf évalue forfaitairement vos 
#        ressources à partir de votre revenu mensuel.

#        On prend la BR des PF pour l'AAH         
    
#        TODO avoir le % d'incapacité ?        
    
    nbh_travaillees = 151.67*12
    smic_annuel = P.cotsoc.gen.smic_h_b*nbh_travaillees

    eligC = ( (self.invC==1) &
              ( (self.ageC >= P.fam.aeeh.age) | (self.ageC >= 16) & (self.revChef > P.fam.af.seuil_rev_taux*smic_annuel)) & 
                (self.ageC <= P.minim.aah.age_legal_retraite ))    

    eligP = ( (self.invP==1) &
              ( (self.ageP >= P.fam.aeeh.age) | (self.ageP >= 16) & (self.revPart > P.fam.af.seuil_rev_taux*smic_annuel)) & 
                (self.ageP <= P.minim.aah.age_legal_retraite ))

    plaf = 12*P.minim.aah.montant*(1 + self.coup + P.minim.aah.tx_plaf_supp*self.NbEnf(P.fam.af.age1, P.fam.af.age2))

    if hasattr(self, "asiC_m") & hasattr(self, "aspaC_m"): 
        self.BRaah = br_pf/12 + self.asiC_m + self.aspaC_m + self.asiP_m + self.aspaP_m
        del self.asiP_m, self.asiC_m, self.aspaP_m, self.aspaC_m
    elif hasattr(self, "mv_m"):     
        self.BRaah = br_pf/12 + self.mv_m
        del self.mv_m

    eligib = ( eligC | eligP )*(self.BRaah <= plaf)
    aah_m = eligib*max_(P.minim.aah.montant - self.BRaah, 0 ) 
    
    # l'aah est exonérée de crds 
    self.aah = aah_m.sum(axis=0)
    
    self.population.openWriteMode()
    self.population.set('aah', self.aah, 'fam', 'chef', table = 'output')
    self.population.close_()

#        Cumul d'allocation
# L'AAH peut être cumulée :
#
#- avec le complément d'AAH (à titre transitoire pour les derniers bénéficiaires, 
#  ce complément étant remplacé par la majoration pour la vie autonome depuis 
#  le 1er juillet 2005) ;
#- avec la majoration pour la vie autonome ;
#- avec le complément de ressources (dans le cadre de la garantie de ressources).
#
# L'AAH n'est pas cumulable avec la perception d'un avantage de vieillesse, 
# d'invalidité, ou d'accident du travail si cet avantage est d'un montant au 
# moins égal à ladite allocation.

def CAAH(self, Param):
    '''
    Complément d'allocation adulte handicapé
    '''
    
#        Conditions
#Pour bénéficier du complément de ressources, l’intéressé doit remplir les conditions
# suivantes :

#- percevoir l’allocation aux adultes handicapés à taux normal ou en
#    complément d’une pension d’invalidité, d’une pension de vieillesse ou
#    d’une rente accident du travail ;
#- avoir un taux d’incapacité égal ou supérieur à 80 % ;
#- avoir une capacité de travail, appréciée par la commission des droits et 
#    de l’autonomie (CDAPH) inférieure à 5 % du fait du handicap ;
#- ne pas avoir perçu de revenu à caractère professionnel depuis un an à la date
#    du dépôt de la demande de complément ;
#- disposer d’un logement indépendant.
#A noter : une personne hébergée par un particulier à son domicile n’est pas 
# considérée disposer d’un logement indépendant, sauf s’il s’agit de son conjoint, 
# de son concubin ou de la personne avec laquelle elle est liée par un pacte civil 
# de solidarité.

#       Complément de ressources Le complément de ressources est
#       destiné aux personnes handicapées dans l’incapacité de
#       travailler Il est égal à la différence entre la garantie de
#       ressources pour les personnes handicapées (GRPH) et l’AAH

    P = Param.minim 
    elig_cpl = zeros((12,self.taille))    # TODO: éligibilité
    
    if self.datesim.year >= 2006: compl = elig_cpl*max_(P.caah.grph-self.aah,0)  
    else : compl = P.caah.cpltx*P.aah.montant*elig_cpl*self.aah
#        else : compl = P.caah.cpltx*P.aah.montant*elig_cpl*self.aah_m 
        # En fait perdure jusqu'en 2008 
 
    # Majoration pour la vie autonome
    # La majoration pour la vie autonome est destinée à permettre aux personnes, en capacité de travailler et au chômage
    # en raison de leur handicap, de pourvoir faire face à leur dépense de logement.
    
#        Conditions d'attribution
#La majoration pour la vie autonome est versée automatiquement aux personnes qui remplissent les conditions suivantes :
#- percevoir l'AAH à taux normal ou en complément d'un avantage vieillesse ou d'invalidité ou d'une rente accident du travail,
#- avoir un taux d'incapacité au moins égal à 80 %,
#- disposer d'un logement indépendant,
#- bénéficier d'une aide au logement (aide personnelle au logement, ou allocation de logement sociale ou familiale), comme titulaire du droit, ou comme conjoint, concubin ou partenaire lié par un Pacs au titulaire du droit,
#- ne pas percevoir de revenu d'activité à caractère professionnel propre.
#Choix entre la majoration ou la garantie de ressources
#La majoration pour la vie autonome n'est pas cumulable avec la garantie de ressources pour les personnes handicapées.
#La personne qui remplit les conditions d'octroi de ces deux avantages doit choisir de bénéficier de l'un ou de l'autre.

    if self.datesim.year >= 2006:        
        elig_mva = zeros((12,self.taille))*(self.aah>0)   # TODO: éligibilité
        mva = P.caah.mva*elig_mva
    else: mva = zeros((12,self.taille))      
    caah = max_(compl,mva)
          
    self.caah = caah.sum(axis=0)
    self.population.openWriteMode()
    self.population.set('caah', self.caah, 'fam', 'chef', table = 'output')
    self.population.close_()
    
def ASS(self, P):
    '''
    Allocation de solidarité spécifique
    '''        
    # TODO majo ass et base ressource
    
#        Les ressources prises en compte pour apprécier ces plafonds, comprennent l'allocation de solidarité elle-même ainsi que les autres ressources de l'intéressé, et de son conjoint, partenaire pacsé ou concubin, soumises à impôt sur le revenu.
#        Ne sont pas prises en compte, pour déterminer le droit à ASS :
#          l'allocation d'assurance chômage précédemment perçue,
#          les prestations familiales,
#          l'allocation de logement,
#          la majoration de l'ASS,
#          la prime forfaitaire mensuelle de retour à l'emploi,
#          la pension alimentaire ou la prestation compensatoire due par l'intéressé.

    
#     Conditions de versement de l'ASS majorée
#      Pour les allocataires admis au bénéfice de l'ASS majorée ( avant le 1er janvier 2004) , le montant de l'ASS majorée est fixé à 22,07 € par jour.
#      Pour mémoire, jusqu'au 31 décembre 2003, pouvaient bénéficier de l'ASS majorée, les allocataires :
#       âgés de 55 ans ou plus et justifiant d'au moins 20 ans d'activité salariée,
#       ou âgés de 57 ans et demi ou plus et justifiant de 10 ans d'activité salariée,
#       ou justifiant d'au moins 160 trimestres de cotisation retraite.

    majo = zeros(self.taille)
    plaf = P.chomage.ass.plaf_seul*self.seul + P.chomage.ass.plaf_coup*self.coup
    montant_mensuel = 30*(P.chomage.ass.montant_plein*not_(majo) 
                          + majo*P.chomage.ass.montant_maj)
    revenus = br_pf + 12*montant_mensuel  # TODO check base ressources
    ass = 12*(montant_mensuel*(revenus<=plaf) 
              + (revenus>plaf)*max_(plaf+montant_mensuel-revenus,0))
    
from core.systemsf import SystemSf, Prestation
from parametres.paramData import XmlReader, Tree2Object

class Pfam(SystemSf):
    
    af_base = Prestation(AF_Base, 'fam', 'Allocations familiales - Base')
    af_majo = Prestation(AF_Majo, 'fam', 'Allocations familiales - Majoration pour age')
    af_forf = Prestation(AF_Base, 'fam', 'Allocations familiales - Forfait 20 ans')
    af      = Prestation(AF, 'fam', label = u"Allocations familiales")

#    rev_pf  = Prestation(Rev_PF, 'Base ressource individuele des prestations familiales')
#    br_pf   = Prestation(Br_PF, 'fam', 'Base ressource des prestations familiales')
#    cf      = Prestation(CF, 'fam', label = u"Complément familiale")

if __name__ == '__main__':
    import datetime
    date = datetime.date(2010,01,01)
    reader = XmlReader('../data/param.xml', date)
    P = Tree2Object(reader.tree)
    print P.fam.af.bmaf
    pfam = Pfam(P)
    print pfam._primitives
    print pfam._inputs
    pfam.calculate('af')
    print pfam.af.get_value()