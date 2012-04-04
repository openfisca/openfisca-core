# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

'''
Created on 22 dec. 2011

@author: benjello
'''
from __future__ import division

import numpy as np
from numpy import exp, ones, zeros, unique, array, dot
from scipy.optimize import fsolve

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

def build_dummies_dict(data):
    '''
    return a dict with unique values as keys and vectors as values
    '''
    unique_val_list = unique(data) 
    output = {}
    for val in unique_val_list:    
        output[val] = (data==val)
    return output

def calmar(data, marge, param = {}, pondini='wprm_init'):
    ''' 
    calmar : calage des poids etant des donnees des marges
      - data is a dict containing individual data
      - pondini (char) is the inital weight
     marge is a dict containing for each var:
      - a scalar var numeric variables
      - a dict with categories key and population 
     param is a dict containing the following keys
      - method : 'linear', 'raking ratio', 'logit'
      - lo     : lower bound on weights ratio  <1
      - up     : upper bound on weights ration >1
      - totalpop : total population. If absent initialized to actual total population
      - use_proportions : default FALSE; if TRUE use proportions if total population from margins doesn't match total population
      - param xtol  : relative precision on lagrangian multipliers. By default xtol = 1.49012e-08 (default fsolve xtol)
      - param maxfev :  maximum number of function evaluation TODO  
    '''   
    # choice of method
    if not 'method' in param:
        param['method'] = 'linear'

    if param['method'] == 'linear': 
        F = linear
        F_prime = linear_prime
    elif param['method'] == 'raking ratio': 
        F =  raking_ratio
        F_prime =  raking_ratio_prime
    elif param['method'] == 'logit':
        if not 'up' in param:
            raise Exception("When method is 'logit', 'up' parameter is needed in param")
        if not 'lo' in param:
            raise Exception("When method is 'logit', 'lo' parameter is needed in param")
        if param['up'] <= 1:
            raise Exception("When method is 'logit', 'up' should be strictly greater than 1")
        if param['lo'] >= 1:
            raise Exception("When method is 'logit', 'lo' should be strictly less than 1")        
        F = lambda x: logit(x, param['lo'], param['up'])
        F_prime = lambda x: logit_prime(x, param['lo'], param['up'])
    else:
        raise Exception("method should be 'linear', 'raking ratio' or 'logit'")


         

    # construction observations matrix
    if 'totalpop' in param:
        totalpop = param['totalpop']
    else:
        totalpop = data[pondini].sum()

    if 'use_proportions' in param:
        use_proportions = param['use_proportions']    
    else:
        use_proportions = False   

    nk = len(data[pondini])

    # number of lagrange parameters (at least total population)
    nj = 1
    
    marge_new = {}
    
    for var, val in marge.iteritems():
        if isinstance(val, dict):
            dummies_dict = build_dummies_dict(data[var])            
            k, pop = 0, 0
            for cat, nb in val.iteritems():
                cat_varname =  var + '_' + str(cat)
                data[cat_varname] = dummies_dict[cat]
                marge_new[cat_varname] = nb
                pop += nb
                k += 1
                nj += 1
            # verification que la population finale est bonne
            if pop != totalpop:
                if use_proportions:
                    import warnings
                    warnings.warn('calmar: categorical variable %s is inconsistent with population; using proportions' % var)
                    for cat, nb in val.iteritems():
                        cat_varname =  var + '_' + str(cat)
                        marge_new[cat_varname] = nb*totalpop/pop
                else:
                    raise Exception('calmar: categorical variable ', var, ' is inconsistent with population')
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
    if 'xtol' in param: 
        xtol = param['xtol']
    else:
        xtol = 1.49012e-08
        
    while (ier==2 or ier==5) and (essai <= 10):
        lambdasol, infodict, ier, mesg = fsolve(constraint, lambda0, fprime=constraint_prime, maxfev= 256, xtol=xtol, full_output=1)
#        print 'ier: ', ier
#        print 'mesg: ', mesg
        lambda0 = 1*lambdasol
        essai += 1
        
    pondfin = d*F( dot(x, lambdasol))

    print "nombre d'essais: ", essai
    return pondfin, lambdasol, marge_new 

def test1():
    data = dict(ident = range(4),
                x = array([5,2,7,6]),
                wprm = array([.5,.5,1,1]))

    marge = dict(x=array(5))
    param = dict(method='linear')
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
    marge = {'g':32, 'f':60, 'j':42, 'k':50, 'z':140}


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

    marge = {'g':{0:60 ,1: 32}, 'j': {0:50,1:42},'z':140}    
    param = dict(method='linear',lo = .0001,up = 1000)
    
    pondfin, lambdasol  = calmar(data,marge,param)
    
    print pondfin
    print lambdasol
    print pondfin/data['wprm']    


def test4():
    # tests large datasets
    n = 10000
    index = np.arange(n)
    val   = index*100
    wprm  = np.random.rand(n)
    
    data = dict(i = index,
                v = val,
                wprm = wprm)

    marge = {'v':sum(1.2*data['wprm']*data['v'])}
    param = dict(method='logit',lo = .001,up = 100)
    
    pondfin, lambdasol  = calmar(data,marge,param,ident='i')
    
    print 'target margin: ', marge['v']
    print 'calib margin',  sum(pondfin*data['v'])
    print pondfin
    print lambdasol
    print pondfin/data['wprm']    
#    info(fsolve)

    from pylab import hist, setp, show, plot
    weight_ratio = pondfin/data['wprm']
    n, bins, patches = hist(weight_ratio, 100, normed=1, histtype='stepfilled')
    setp(patches, 'facecolor', 'g', 'alpha', 0.75)
    show()
    plot(wprm, pondfin/wprm, 'x')
    show()

if __name__ == '__main__':
    test3()
