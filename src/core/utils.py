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
import os
from xml.dom import minidom
from numpy import maximum as max_, minimum as min_
import numpy as np
from bisect import bisect_right
from Config import CONF, VERSION
import pickle
from datetime import datetime
from pandas import DataFrame


class Enum(object):
    def __init__(self, varlist, start = 0):
        self._vars = {}
        self._nums = {}
        self._count = 0
        for var in varlist:
            self._vars.update({self._count + start:var})
            self._nums.update({var: self._count + start})
            self._count += 1
            
    def __getitem__(self, var):
        return self._nums[var]

    def __iter__(self):
        return self.itervars()
    
    def itervars(self):
        for key, val in self._vars.iteritems():
            yield (val, key)
            
    def itervalues(self):
        for val in self._vars:
            yield val

def handle_output_xml(doc, tree, model, unit = 'men'):
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
                handle_output_xml(element, child, model, unit)
    else:

        idx = model.index[unit]
        inputs = model._inputs
        enum = inputs.description.get_col('qui'+unit).enum
        people = [x[1] for x in enum]
        if tree.code in model.col_names:
            model.calculate(tree.code)
            val = model.get_value(tree.code, idx, opt = people, sum_ = True)
        elif tree.code in inputs.col_names:
            val = inputs.get_value(tree.code, idx, opt = people, sum_ = True)
        else:
            raise Exception('%s was not find in model nor in inputs' % tree.code)
        tree.setVals(val)

            
def gen_output_data(model, filename = None):
    '''
    Generates output data according to filename or totaux.xml
    '''
    if filename is None:
        country = CONF.get('simulation', 'country')
        totals_fname = os.path.join(country,'totaux.xml')
    else:
        totals_fname = filename
    
    _doc = minidom.parse(totals_fname)
    tree = OutNode('root', 'root')
    handle_output_xml(_doc, tree, model)
    return tree

def gen_aggregate_output(model):

    out_dct = {}
    inputs = model._inputs
    unit = 'men'
    idx = model.index[unit]
    enum = inputs.description.get_col('qui'+unit).enum
    people = [x[1] for x in enum]

    model.calculate()

    varlist = set(['wprm', 'typ_men', 'so', 'typmen15', 'tu99', 'ddipl', 'ageq', 'cstotpragr', 'decile', 'champm'])
    for varname in model.col_names.union(varlist):
        if varname in model.col_names:
            if model.description.get_col(varname)._unit != unit:
                val = model.get_value(varname, idx, opt = people, sum_ = True)    
            else:
                val = model.get_value(varname, idx)
        elif varname in inputs.col_names:
            val = inputs.get_value(varname, idx)
        else:
            raise Exception('%s was not find in model nor in inputs' % varname)
        
        out_dct[varname] = val      
    # TODO: should take care the variables that shouldn't be summed automatically
    # MBJ: should we introduce a scope (men, fam, ind) in a the definition of columns ?

    out_table = DataFrame(out_dct)
    return out_table

class OutNode(object):
    def __init__(self, code, desc, shortname = '', vals = 0, color = (0,0,0), typevar = 0, parent = None):
        self.parent = parent
        self.children = []
        self.code = code
        self.desc = desc
        self.color = color
        self.visible = 0
        self.typevar = typevar
        self._vals = vals
        self._taille = 0
        if shortname: 
            self.shortname = shortname
        else: 
            self.shortname = code
        
    def addChild(self, child):
        self.children.append(child)
        if child.color == (0,0,0):
            child.color = self.color
        child.setParent(self)

    def setParent(self, parent):
        self.parent = parent

    def child(self, row):
        return(self.children[row])

    def childCount(self):
        return len(self.children)

    def row(self):
        if self.parent is not None:
            return self.parent.children.index(self)

    def setLeavesVisible(self):
        for child in self.children:
            child.setLeavesVisible()
        if (self.children and (self.code !='revdisp')) or (self.code == 'nivvie'):
            self.visible = 0
        else:
            self.visible = 1
    
    def partiallychecked(self):
        if self.children:
            a = True
            for child in self.children:
                a = a and (child.partiallychecked() or child.visible)
            return a
        return False
    
    def hideAll(self):
        if self.code == 'revdisp':
            self.visible = 1
        else:
            self.visible = 0
        for child in self.children:
            child.hideAll()
    
    def setHidden(self, changeParent = True):
        # les siblings doivent être dans le même
        if self.partiallychecked():
            self.visible = 0
            return
        for sibling in self.parent.children:
            sibling.visible = 0
            for child in sibling.children:
                child.setHidden(False)
        if changeParent:
            self.parent.visible = 1
                    
    def setVisible(self, changeSelf = True, changeParent = True):
        if changeSelf:
            self.visible = 1
        if self.parent is not None:
            for sibling in self.parent.children:
                if not (sibling.partiallychecked() or sibling.visible ==1):
                    sibling.visible = 1
            if changeParent:
                self.parent.setVisible(changeSelf = False)


    def getVals(self):
        return self._vals

    def setVals(self, vals):
        dif = vals - self._vals
        self._vals = vals
        self._taille = len(vals)
        if self.parent:
            self.parent.setVals(self.parent.vals + dif)
    
    vals = property(getVals, setVals)
        
    def __getitem__(self, key):
        if self.code == key:
            return self
        for child in self.children:
            val = child[key]
            if not val is None:
                return val
    
    def log(self, tabLevel=-1):
        output     = ""
        tabLevel += 1
        
        for i in range(tabLevel):
            output += "\t"
        
        output += "|------" + self.code + "\n"
        
        for child in self.children:
            output += child.log(tabLevel)
        
        tabLevel -= 1
        output += "\n"
        
        return output

    def __repr__(self):
        return self.log()

    def difference(self, other):
       
        self.vals -=  other.vals
        for child in self.children:
            child.difference(other[child.code])

    def __iter__(self):
        return self.inorder()
    
    def inorder(self):
        for child in self.children:
            for x in child.inorder():
                yield x
        yield self



############################################################################
## Bareme and helper functions for Baremes
############################################################################

class Bareme(object):
    '''
    Object qui contient des tranches d'imposition en taux marginaux et en taux moyen
    '''
    def __init__(self, name = 'untitled Bareme', option = None, unit = None):
        super(Bareme, self).__init__()
        self._name = name
        self._tranches = []
        self._nb = 0
        self._tranchesM = []
        # if _linear_taux_moy is 'False' (default), the output is computed with a constant marginal tax rate in each bracket
        # set _linear_taux_moy to 'True' to compute the output with a linear interpolation on average tax rate
        self._linear_taux_moy = False
        self._option = option
        self.unit = unit

    @property
    def option(self):
        return self._option
 
    def setOption(self, option):
        self._option = option

    @property
    def nb(self):
        return self._nb
    
    @property
    def seuils(self):
        return [x[0] for x in self._tranches]

    @property
    def taux(self):
        return [x[1] for x in self._tranches]

    def setSeuil(self, i, value):
        self._tranches[i][0] = value
        self._tranches.sort()

    def setTaux(self, i, value):
        self._tranches[i][1] = value

    @property
    def seuilsM(self):
        return [x[0] for x in self._tranchesM]

    @property
    def tauxM(self):
        return [x[1] for x in self._tranchesM]

    def setSeuilM(self, i, value):
        self._tranchesM[i][0] = value
        self._tranchesM.sort()

    def setTauxM(self, i, value):
        self._tranchesM[i][1] = value
    
    
    def multTaux(self, factor):
        for i in range(self._nb):
            self.setTaux(i,factor*self.taux[i])

    def multSeuils(self, factor):
        '''
        Returns a new instance of Bareme with scaled 'seuils' and same 'taux'
        '''
        b = Bareme(self._name, option = self._option, unit = self.unit)
        for i in range(self.nb):
            b.addTranche(factor*self.seuils[i], self.taux[i])
        return b
        
    def addBareme(self, bareme):
        if bareme.nb>0: # Pour ne pas avoir de problèmes avec les barèmes vides
            for seuilInf, seuilSup, taux  in zip(bareme.seuils[:-1], bareme.seuils[1:] , bareme.taux):
                self.combineTranche(taux, seuilInf, seuilSup)
            self.combineTranche(bareme.taux[-1],bareme.seuils[-1])  # Pour traiter le dernier seuil

    def combineTranche(self, taux, seuilInf=0, seuilSup=False ):
        # Insertion de seuilInf et SeuilSup sans modfifer les taux
        if not seuilInf in self.seuils:
            index = bisect_right(self.seuils, seuilInf)-1
            self.addTranche(seuilInf, self.taux[index]) 
        
        if seuilSup and not seuilSup in self.seuils:
                index = bisect_right(self.seuils,seuilSup)-1
                self.addTranche(seuilSup, self.taux[index]) 

        # On utilise addTranche pour ajouter les taux où il le faut        
        i = self.seuils.index(seuilInf)
        if seuilSup: j = self.seuils.index(seuilSup)-1 
        else: j = self._nb-1
        while (i <= j):
            self.addTranche(self.seuils[i], taux)
            i +=1
            
    def addTranche(self, seuil, taux):
        if seuil in self.seuils:
            i = self.seuils.index(seuil)
            self.setTaux(i, self.taux[i] + taux)
        else:
            self._tranches.append([seuil,taux])
            self._tranches.sort()
            self._nb = len(self._tranches)

    def rmvTranche(self):
        self._tranches.pop()
        self._nb = len(self._tranches)

    def addTrancheM(self, seuil, taux):
        if seuil in self.seuilsM:
            i = self.seuilsM.index(seuil)
            self.setTauxM(i, self.tauxM[i] + taux)
        else:
            self._tranchesM.append([seuil,taux])
    
    def marToMoy(self):
        self._tranchesM = []
        I, k = 0, 0
        if self.nb > 0:
            for seuil, taux in self:
                if k == 0:
                    sprec = seuil
                    tprec = taux
                    k += 1
                    continue            
                I += tprec*(seuil - sprec)
                self.addTrancheM(seuil, I/seuil)
                sprec = seuil
                tprec = taux
            self.addTrancheM('Infini', taux)

    def moyToMar(self):
        self._tranches = []
        Iprev, sprev = 0, 0
        z = zip(self.seuilsM, self.tauxM)
        for seuil, taux in z:
            if not seuil == 'Infini':
                I = taux*seuil
                self.addTranche(sprev, (I-Iprev)/(seuil-sprev))
                sprev = seuil
                Iprev = I
        self.addTranche(sprev, taux)
    
    def inverse(self):
        '''
        Returns a new instance of Bareme
        Inverse un barème: étant donné des tranches et des taux exprimés en fonction
        du brut, renvoie un barème avec les tranches et les taux exprimé en net.
          si revnet  = revbrut - BarmMar(revbrut, B)
          alors revbrut = BarmMar(revnet, B.inverse())
        seuil : seuil de revenu brut
        seuil imposable : seuil de revenu imposable/déclaré
        theta : ordonnée à l'origine des segments des différentes tranches dans une 
                représentation du revenu imposable comme fonction linéaire par 
                morceaux du revenu brut
        '''
        inverse = Bareme(self._name + "'")  # En fait 1/(1-taux_global)
        seuilImp, taux = 0, 0
        for seuil, taux in self:
            if seuil==0: theta, tauxp = 0,0
            # On calcul le seuil de revenu imposable de la tranche considérée
            seuilImp = (1-tauxp)*seuil + theta    
            inverse.addTranche(seuilImp, 1/(1-taux))
            theta = (taux - tauxp)*seuil + theta
            tauxp = taux # taux précédent
        return inverse
    
    def __iter__(self):
        self._seuilsIter = iter(self.seuils)
        self._tauxIter = iter(self.taux)
        return self

    def next(self):
        return self._seuilsIter.next(), self._tauxIter.next()
    
    def __str__(self):
        output = self._name + '\n'
        for i in range(self._nb):
            output += str(self.seuils[i]) + '  ' + str(self.taux[i]) + '\n'
        return output

    def __eq__(self, other):
        return self._tranches == other._tranches

    def __ne__(self, other):
        return self._tranches != other._tranches
    
    def calc(self, assiette, getT = False):
        '''
        Calcule un impôt selon le barême non linéaire exprimé en tranches de taux marginaux.
        'assiette' est l'assiette de l'impôt, en colonne
        '''
        k = self.nb
        n = len(assiette)
        if not self._linear_taux_moy:
            assi = np.tile(assiette, (k, 1)).T
            seui = np.tile(np.hstack((self.seuils, np.inf)), (n, 1))
            a = max_(min_(assi, seui[:, 1:]) - seui[:,:-1], 0)
            i = np.dot(self.taux,a.T)
            if getT:
                t = np.squeeze(max_(np.dot((a>0), np.ones((k, 1)))-1, 0))
                return i, t
            else:
                return i
        else:
            if len(self.tauxM) == 1:
                i = assiette*self.tauxM[0]
            else:
                assi = np.tile(assiette, (k-1, 1)).T
                seui = np.tile(np.hstack(self.seuils), (n, 1))
                k = self.t_x().T
                a = (assi >= seui[:,:-1])*(assi < seui[:, 1:])
                A = np.dot(a, self.t_x().T)
                B = np.dot(a, np.array(self.seuils[1:]))
                C = np.dot(a, np.array(self.tauxM[:-1]))
                i = assiette*(A*(assiette-B) + C) + max_(assiette - self.seuils[-1], 0)*self.tauxM[-1] + (assiette >= self.seuils[-1])*self.seuils[-1]*self.tauxM[-2]
            if getT:
                t = np.squeeze(max_(np.dot((a>0), np.ones((k, 1)))-1, 0))
                return i, t
            else:
                return i

    def t_x(self):
        s = self.seuils
        t = [0]
        t.extend(self.tauxM[:-1])
        s = np.array(s)
        t = np.array(t)
        return (t[1:]-t[:-1])/(s[1:]-s[:-1])


class BaremeDict(dict):
    '''
    A dict of Bareme's
    '''
    def __init__(self, name = None, tree2object = None):
        
        super(BaremeDict, self).__init__()

        if name is None:
            raise Exception("BaremeDict instance needs a name to be created")
        else:
            self._name = name
        
        if tree2object is not None:
            self.init_from_param(tree2object) 
        
    
    def init_from_param(self, tree2object):
        '''
        Init a BaremeDict form a Tree2Object
        '''
        from parametres.paramData import Tree2Object
        
        if isinstance(tree2object, Bareme):
            self[tree2object._name] = tree2object 
        elif isinstance(tree2object, Tree2Object):
            for key, bar in tree2object.__dict__.iteritems():
                if isinstance(bar, Bareme):
                    self[key] = bar
                elif isinstance(bar, Tree2Object):
                    new = BaremeDict(key, bar)
                    self[key] = new   
        
            
def combineBaremes(bardict, name = None):
    '''
    Combine all the Baremes in the BaremeDict in a signle Bareme
    '''
    if name is None:
        name = 'Combined ' + bardict._name
    baremeTot = Bareme(name = name)
    baremeTot.addTranche(0,0)
    for name, bar in bardict.iteritems():
        if isinstance(bar, Bareme):
            baremeTot.addBareme(bar)
        else: 
            combineBaremes(bar, baremeTot)
    return baremeTot




def scaleBaremes(bar_dict, factor):
    '''
    Scales all the Bareme in the BarColl
    '''
#    from parametres.paramData import Tree2Object
    
    if isinstance(bar_dict, Bareme):
        return bar_dict.multSeuils(factor)
    
    if isinstance(bar_dict, BaremeDict):
        out = BaremeDict(name = bar_dict._name)
    
        for key, bar in bar_dict.iteritems():
            if isinstance(bar, Bareme):
                out[key] = bar.multSeuils(factor)
            elif isinstance(bar, BaremeDict):
                out[key] = scaleBaremes(bar, factor)
            else:
                setattr(out, key, bar)
        return out
    


def lower_and_underscore(string):
    r = str()
    for l in string:
        if l.isupper():
            r += "_" + l.lower()
        else:
            r += l
    return r



############################################################################
## Helper functions for stats
############################################################################
# from http://pastebin.com/KTLip9ee
def mark_weighted_percentiles(a, labels, weights, method, return_quantiles=False):
# a is an input array of values.
# weights is an input array of weights, so weights[i] goes with a[i]
# labels are the names you want to give to the xtiles
# method refers to which weighted algorithm. 
#      1 for wikipedia, 2 for the stackexchange post.

# The code outputs an array the same shape as 'a', but with
# labels[i] inserted into spot j if a[j] falls in x-tile i.
# The number of xtiles requested is inferred from the length of 'labels'.


# First method, "vanilla" weights from Wikipedia article.
    if method == 1:
    
        # Sort the values and apply the same sort to the weights.
        N = len(a)
        sort_indx = np.argsort(a)
        tmp_a = a[sort_indx].copy()
        tmp_weights = weights[sort_indx].copy()
    
        # 'labels' stores the name of the x-tiles the user wants,
        # and it is assumed to be linearly spaced between 0 and 1
        # so 5 labels implies quintiles, for example.
        num_categories = len(labels)
        breaks = np.linspace(0, 1, num_categories+1)
    
        # Compute the percentile values at each explicit data point in a.
        cu_weights = np.cumsum(tmp_weights)
        p_vals = (1.0/cu_weights[-1])*(cu_weights - 0.5*tmp_weights)
    
        # Set up the output array.
        ret = np.repeat(0, len(a))
        if(len(a)<num_categories):
            return ret
    
        # Set up the array for the values at the breakpoints.
        quantiles = []
    
    
        # Find the two indices that bracket the breakpoint percentiles.
        # then do interpolation on the two a_vals for those indices, using
        # interp-weights that involve the cumulative sum of weights.
        for brk in breaks:
            if brk <= p_vals[0]: 
                i_low = 0
                i_high = 0
            elif brk >= p_vals[-1]:
                i_low = N-1
                i_high = N-1
            else:
                for ii in range(N-1):
                    if (p_vals[ii] <= brk) and (brk < p_vals[ii+1]):
                        i_low  = ii
                        i_high = ii + 1       
    
            if i_low == i_high:
                v = tmp_a[i_low]
            else:
                # If there are two brackets, then apply the formula as per Wikipedia.
                v = tmp_a[i_low] + ((brk-p_vals[i_low])/(p_vals[i_high]-p_vals[i_low]))*(tmp_a[i_high]-tmp_a[i_low])
    
            # Append the result.
            quantiles.append(v)
    
        # Now that the weighted breakpoints are set, just categorize
        # the elements of a with logical indexing.
        for i in range(0, len(quantiles)-1):
            lower = quantiles[i]
            upper = quantiles[i+1]
            ret[ np.logical_and(a>=lower, a<upper) ] = labels[i] 
    
        #make sure upper and lower indices are marked
        ret[a<=quantiles[0]] = labels[0]
        ret[a>=quantiles[-1]] = labels[-1]
    
        return ret
    
    # The stats.stackexchange suggestion.
    elif method == 2:
    
        N = len(a)
        sort_indx = np.argsort(a)
        tmp_a = a[sort_indx].copy()
        tmp_weights = weights[sort_indx].copy()
    
    
        num_categories = len(labels)
        breaks = np.linspace(0, 1, num_categories+1)
    
        cu_weights = np.cumsum(tmp_weights)
    
        # Formula from stats.stackexchange.com post.
        s_vals = [0.0]
        for ii in range(1,N):
            s_vals.append( ii*tmp_weights[ii] + (N-1)*cu_weights[ii-1])
        s_vals = np.asarray(s_vals)
    
        # Normalized s_vals for comapring with the breakpoint.
        norm_s_vals = (1.0/s_vals[-1])*s_vals 
    
        # Set up the output variable.
        ret = np.repeat(0, N)
        if(N < num_categories):
            return ret
    
        # Set up space for the values at the breakpoints.
        quantiles = []
    
    
        # Find the two indices that bracket the breakpoint percentiles.
        # then do interpolation on the two a_vals for those indices, using
        # interp-weights that involve the cumulative sum of weights.
        for brk in breaks:
            if brk <= norm_s_vals[0]: 
                i_low = 0
                i_high = 0
            elif brk >= norm_s_vals[-1]:
                i_low = N-1
                i_high = N-1
            else:
                for ii in range(N-1):
                    if (norm_s_vals[ii] <= brk) and (brk < norm_s_vals[ii+1]):
                        i_low  = ii
                        i_high = ii + 1   
    
            if i_low == i_high:
                v = tmp_a[i_low]
            else:
                # Interpolate as in the method 1 method, but using the s_vals instead.
                v = tmp_a[i_low] + (( (brk*s_vals[-1])-s_vals[i_low])/(s_vals[i_high]-s_vals[i_low]))*(tmp_a[i_high]-tmp_a[i_low])
            quantiles.append(v)
    
        # Now that the weighted breakpoints are set, just categorize
        # the elements of a as usual. 
        for i in range(0, len(quantiles)-1):
            lower = quantiles[i]
            upper = quantiles[i+1]
            ret[ np.logical_and( a >= lower, a < upper ) ] = labels[i] 
    
        #make sure upper and lower indices are marked
        ret[a<=quantiles[0]] = labels[0]
        ret[a>=quantiles[-1]] = labels[-1]
    
        if return_quantiles:
            return ret, quantiles
        else:
            return ret
        

from numpy import cumsum, ones, sort, random       
from pandas import DataFrame

def gini(values, weights = None, bin_size = None):
    '''
    Gini coefficient (normalized to 1)
    Using fastgini formula :


                      i=N      j=i
                      SUM W_i*(SUM W_j*X_j - W_i*X_i/2)
                      i=1      j=1
          G = 1 - 2* ----------------------------------
                           i=N             i=N
                           SUM W_i*X_i  *  SUM W_i
                           i=1             i=1


        where observations are sorted in ascending order of X.
    
    From http://fmwww.bc.edu/RePec/bocode/f/fastgini.html
    '''
    if weights is None:
        weights = ones(len(values))
        
    df = DataFrame( {'x': values, 'w':weights} )    
    df = df.sort_index(by='x')
    x = df['x']
    w = df['w']
    wx = w*x
    
    cdf = cumsum(wx)-0.5*wx  
    numerator = (w*cdf).sum()
    denominator = ( (wx).sum() )*( w.sum() )
    gini = 1 - 2*( numerator/denominator) 
    
    return gini


def lorenz(values, weights = None):
    '''
    Computes Lorenz Curve coordinates
    '''
    if weights is None:
        weights = ones(len(values))
        
    df = DataFrame( {'v': values, 'w':weights} )    
    df = df.sort_index( by = 'v')    
    x = cumsum(df['w'])
    x = x/float(x[-1:])
    y = cumsum( df['v']*df['w'] )
    y = y/float(y[-1:])
    
    return x, y


def pseudo_lorenz(values, ineq_axis, weights = None):
    '''
    Computes The pseudo Lorenz Curve coordinates
    '''
    if weights is None:
        weights = ones(len(values))
    df = DataFrame( {'v': values, 'a': ineq_axis, 'w':weights} )    
    df = df.sort_index( by = 'a')
    x = cumsum(df['w'])
    x = x/float(x[-1:])
    y = cumsum( df['v']*df['w'] )
    y = y/float(y[-1:])
    
    return x, y


def kakwani(values, ineq_axis, weights = None):
    '''
    Computes the Kakwani index
    '''
    if weights is None:
        weights = ones(len(values))
    
#    sign = -1
#    if tax == True: 
#        sign = -1
#    else:
#        sign = 1
        
    PLCx, PLCy = pseudo_lorenz(values, ineq_axis, weights)
    LCx, LCy = lorenz(ineq_axis, weights)
    
    del PLCx
    
    from scipy.integrate import simps
    
    return simps( (LCy - PLCy), LCx)
        

from widgets.matplotlibwidget import MatplotlibWidget

def test():
    import sys
    from PyQt4.QtGui import QMainWindow, QApplication
    
    class ApplicationWindow(QMainWindow):
        def __init__(self):
            QMainWindow.__init__(self)
            self.mplwidget = MatplotlibWidget(self, title='Example',
                                              xlabel='x',
                                              ylabel='y',
                                              hold=True)
            self.mplwidget.setFocus()
            self.setCentralWidget(self.mplwidget)
            self.plot(self.mplwidget.axes)
            
        def plot(self, axes):
            a = random.uniform(low=0,high=1,size=400)
            from numpy import exp
            #v = a
            v = -(exp(10*a).max() - exp(10*a)) 
            print v.sum()
            
            x, y = lorenz(a)
            print kakwani(v,a)
            x2, z = pseudo_lorenz(v,a)
            axes.plot(x,y, label='L')
            axes.plot(x2,z, label='PL')
            axes.plot(x,x)
            axes.legend()
        
    app = QApplication(sys.argv)
    win = ApplicationWindow()
    win.show()
    sys.exit(app.exec_())
    

def of_import(module, classname, country = None):
    '''
    Returns country specific class found in country module
    '''
    if country is None:
        country = CONF.get('simulation', 'country')
#    This is a failed tentative to overcome py2exe problem
#    import sys
#    src_dir = os.path.dirname(sys.argv[0])
#    imports_dir = os.path.join(src_dir, country)
#    print imports_dir
#    sys.path.insert(0, imports_dir)
#    

    _temp = __import__(country + '.' + module, globals = globals(), locals = locals(), fromlist = [classname], level=-1)
    
#    from tentative to overcome py2exe problem
#    sys.path.pop(0)
    return getattr(_temp, classname, None)


if __name__=='__main__':

    test()

