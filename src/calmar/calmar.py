# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

'''
Created on 22 dec. 2011

@author: benjello
'''
from __future__ import division

from numpy import exp, ones, zeros, unique, array, dot, float
from scipy import info
from scipy.optimize import fsolve
from copy import deepcopy
from numpy.random import rand

def linear(u):
    return 1+u
   
def linear_prime(u):
    return ones(u.shape, dtype = float) 
   
def raking_ratio(u):
    return exp(u)
        
def raking_ratio_prime(u):
    return exp(u)        
        
def logit(u,low,up):
    a=(up-low)/((1-low)*(up-1))
    return (low*(up-1)+up*(1-low)*exp(a*u))/(up-1+(1-low)*exp(a*u))

def logit_prime(u,low,up):
    a=(up-low)/((1-low)*(up-1))
    return ( (a*up*(1-low)*exp(a*u))*(up-1+(1-low)*exp(a*u))-
              (low*(up-1)+up*(1-low)*exp(a*u))*(1-low)*a*exp(a*u) )/(up-1+(1-low)*exp(a*u))**2

def build_dummies_matrix(data):
    unique_val_list = unique(data)  
    output = zeros((len(data),len(unique_val_list)))
    for i in range(len(unique_val_list)):    
        output[:,i] = (data==unique_val_list[i])
    return output

def calmar(data, marge, param={'method':'linear'}, pondini='wprm', ident='ident'):
    ''' 
    calmar : calage des poids etant des donnees des marges
     data est une structure contenant
      - pondini (char) est le nom la variable poids initial
      - ident   (char) est le nom de la variable des identifiants
     marge is a dict containing for each var:
      - a scalar var numeric variables
      - a dict with categories key and population 
     param est un dictionnaire contenant
      - method 
      - lo    borne inferieur sur le rapport des poids <1
      - up    borne inferieur sur le rapport des poids >1
      - totalpop   population totale si absent on l'initialise a la
                         somme des poids
      - param.prec     TODO
      - param.maxiter  TODO
    '''   
    # choice of method

    if param['method'] == 'linear': 
        F = linear
        F_prime = linear_prime
    elif param['method'] == 'raking ratio': 
        F =  raking_ratio
        F_prime =  raking_ratio_prime
    elif param['method'] == 'logit': 
        F = lambda x: logit(x, param['lo'], param['up'])
        F_prime = lambda x: logit_prime(x, param['lo'], param['up'])
    else:
        raise Exception("method should be 'linear', 'raking ratio' or 'logit'")

    # construction observations matrix
    if 'totalpop' in param:
        totalpop = param['totalpop']
    else:
        totalpop = data[pondini].sum()

    nk = len(data[ident])

    # number of lagrange parameters (at least total population)
    nj = 1
    
    marge_new = {}
    
    for var, val in marge.iteritems():
        if isinstance(val, dict):
            dummies_matrix = build_dummies_matrix(data[var])
            # verification que la population finale est bonne
            if marge[var].sum()!=totalpop:
                raise Exception('calmar: categorical variable ', var, ' is inconsistent with population')
            
            k = 0
            for cat, nb in val.iteritems():
                cat_varname =  var + cat
                data[cat_varname] = dummies_matrix[:,k]
                marge_new[cat_varname] = nb
                k += 1
                nj += 1
                    
        else:
            marge_new[var] = val
            nj += 1

    # On conserve systematiquement la population  
    if  hasattr(data,'dummy_is_in_pop'):
        raise Exception('dummy_is_in_pop is not a valid variable name') 
        
    data['dummy_is_in_pop'] = ones(nk)
    marge_new['dummy_is_in_pop'] = totalpop

    # paramètres de Lagrange initialisés à zéro
    lambda0 = zeros(nj)
    
    # initial weights
    d = data[pondini]
    x = zeros((nk, nj)) # nb obs x nb constraints
    xmarges = zeros(nj)
    
    j=0
    for var , val in marge_new.iteritems():
        x[:,j] = data[var]
        xmarges[j] = val
        j += 1

    # Résolution des équations du premier ordre
    constraint = lambda l: dot(d*F(dot(x, l)), x) - xmarges
    constraint_prime = lambda l: dot(d*( x.T*F_prime( dot(x, l))), x )
    ## le jacobien celui ci-dessus est constraintprime = @(l) x*(d.*Fprime(x'*l)*x');
    
    essai, ier = 0, 2
    while (ier==2 or ier==5) and (essai <= 5):
        lambdasol, infodict, ier, mesg = fsolve(constraint, lambda0, fprime=constraint_prime, maxfev= 256, full_output=1)
        print 'ier: ', ier
        print 'mesg: ', mesg
        lambda0 = 1*lambdasol
        essai += 1
        
    pondfin = d*F( dot(x, lambdasol))

    print "nombre d'essais: ", essai
    return pondfin, lambdasol 

def test1():
    data = dict(ident = range(1,2+1),
                x = array([1,2]),
                wprm = 1*ones((2)))

    marge = dict(x=array(5))
    param = dict(method='raking ratio',lo=.3,up=3)
#    param = dict(method='linear',lo=1/3,up=3)

    pondfin, lambdasol  = calmar(data,marge,param)

    print 'initial weights: ', data['wprm'] 
    print 'final weights: ',  pondfin
    print 'lambdas:', lambdasol
    print 'target margin: ', marge
    print 'new margin: ', sum(pondfin*data['x']) 
    print pondfin/data['wprm']    


def test2():
    data = dict(i = array([1,2,3,4,5,6,7,8,9,10,11]),
                g = array([1,1,1,0,0,0,0,1,0, 0, 0]),
                f = array([0,0,0,1,1,1,1,0,1, 1, 1]),
                j = array([1,0,0,1,1,0,0,0,1, 0, 0]),
                k = array([0,1,1,0,0,1,1,1,0, 1, 1]),
                z = array([1,2,3,1,3,2,2,2,2, 2, 2]),
                wprm = array([10,1,1,11,13,7,8,8,9,10,14]))
    marge = dict(g =array(32), f =array(60), j =array(42), k=array(50), z =array(140))


    param = dict(method='linear')
#    param = dict(method='raking ratio')
#    param = dict(method='logit',lo=.3,up=3)
    pondfin, lambdasol  = calmar(data,marge,param,ident='i')
    print pondfin
    print lambdasol
    
    print 'initial weights: ', data['wprm'] 
    print 'final weights: ',  pondfin
    print 'lambdas:', lambdasol
    print 'target margin: ', marge
    print 'new margin: ', sum(pondfin*data['z']) 
    print pondfin/data['wprm']    
    

def test3():
    # idem test2 but tests categorical variables
    data = dict(i = array([1,2,3,4,5,6,7,8,9,10,11]),
                g = array([1,1,1,0,0,0,0,1,0, 0, 0]),
                j = array([1,0,0,1,1,0,0,0,1, 0, 0]),
                z = array([1,2,3,1,3,2,2,2,2, 2, 2]),
                wprm = array([10,1,1,11,13,7,8,8,9,10,14]))

    marge = dict(g =array([60,32]), j =array([50,42]),z =array(140))    
    param = dict(method='linear',lo = .0001,up = 1000)
    
    pondfin, lambdasol  = calmar(data,marge,param,ident='i')
    
    print pondfin
    print lambdasol
    print pondfin/data['wprm']    


def test4():
    # tests large datasets
    n = 100000
    index = array(range(1,n+1))
    val   = index*100
    wprm  = rand(n)
    
    data = dict(i = index,
                v = val,
                wprm = wprm)

    marge = dict(v = sum(1.2*data['wprm']*data['v']))    
    param = dict(method='logit',lo = .001,up = 100)
    
    pondfin, lambdasol  = calmar(data,marge,param,ident='i')
    
    print 'target margin: ', marge['v']
    print 'calib margin',  sum(pondfin*data['v'])
    print pondfin
    print lambdasol
    print pondfin/data['wprm']    
#    info(fsolve)

    from pylab import hist, setp, figure, show
    weight_ratio = pondfin/data['wprm']
    n, bins, patches = hist(weight_ratio, 100, normed=1, histtype='stepfilled')
    setp(patches, 'facecolor', 'g', 'alpha', 0.75)
    show()

if __name__ == '__main__':
    test3()
