# -*- coding: utf-8 -*-


from __future__ import division

import logging
import operator

from numpy import exp, ones, zeros, unique, array, dot, float64
try:
    from scipy.optimize import fsolve
except:
    pass


log = logging.getLogger(__name__)


def linear(u):
    return 1 + u


def linear_prime(u):
    return ones(u.shape, dtype = float)


def raking_ratio(u):
    return exp(u)


def raking_ratio_prime(u):
    return exp(u)


def logit(u, low, up):
    a = (up - low) / ((1 - low) * (up - 1))
    return (low * (up - 1) + up * (1 - low) * exp(a * u)) / (up - 1 + (1 - low) * exp(a * u))


def logit_prime(u, low, up):
    a = (up - low) / ((1 - low) * (up - 1))
    return ((a * up * (1 - low) * exp(a * u)) * (up - 1 + (1 - low) * exp(a * u)) -
        (low * (up - 1) + up * (1 - low) * exp(a * u)) * (1 - low) * a * exp(a * u)) \
        / (up - 1 + (1 - low) * exp(a * u)) ** 2


def build_dummies_dict(data):
    '''
    return a dict with unique values as keys and vectors as values
    '''
    unique_val_list = unique(data)
    output = {}
    for val in unique_val_list:
        output[val] = (data == val)
    return output


def calmar(data_in, margins, parameters = {}, pondini='wprm_init'):
    '''
    Calibraters weights according to some margins
      - data_in is a dict containing individual data
      - pondini (char) is the inital weight
     margins is a dict containing for each var:
      - a scalar var numeric variables
      - a dict with categories key and population
      - eventually a key named total_population : total population. If absent initialized to actual total population
     parameters is a dict containing the following keys
      - method : 'linear', 'raking ratio', 'logit'
      - lo     : lower bound on weights ratio  <1
      - up     : upper bound on weights ration >1
      - use_proportions : default FALSE; if TRUE use proportions if total population from margins doesn't match total
        population
      - param xtol  : relative precision on lagrangian multipliers. By default xtol = 1.49012e-08 (default fsolve xtol)
      - param maxfev :  maximum number of function evaluation TODO
    '''

    # remove null weights and keep original data
    data = dict()
    is_weight_not_null = (data_in[pondini] > 0)
    for a in data_in:
        data[a] = data_in[a][is_weight_not_null]

    if not margins:
        raise Exception("Calmar requires non empty dict of margins")

    # choice of method
    if 'method' not in parameters:
        parameters['method'] = 'linear'

    if parameters['method'] == 'linear':
        F = linear
        F_prime = linear_prime
    elif parameters['method'] == 'raking ratio':
        F = raking_ratio
        F_prime = raking_ratio_prime
    elif parameters['method'] == 'logit':
        if 'up' not in parameters:
            raise Exception("When method is 'logit', 'up' parameter is needed in parameters")
        if 'lo' not in parameters:
            raise Exception("When method is 'logit', 'lo' parameter is needed in parameters")
        if parameters['up'] <= 1:
            raise Exception("When method is 'logit', 'up' should be strictly greater than 1")
        if parameters['lo'] >= 1:
            raise Exception("When method is 'logit', 'lo' should be strictly less than 1")

        def F(x):
            return logit(x, parameters['lo'], parameters['up'])

        def F_prime(x):
            return logit_prime(x, parameters['lo'], parameters['up'])
    else:
        raise Exception("method should be 'linear', 'raking ratio' or 'logit'")
    # construction observations matrix
    if 'total_population' in margins:
        total_population = margins.pop('total_population')
    else:
        total_population = data[pondini].sum()

    if 'use_proportions' in parameters:
        use_proportions = parameters['use_proportions']
    else:
        use_proportions = False

    nk = len(data[pondini])

    # number of Lagrange parameters (at least total population)
    nj = 1

    margins_new = {}
    margins_new_dict = {}
    for var, val in margins.iteritems():
        if isinstance(val, dict):
            dummies_dict = build_dummies_dict(data[var])
            k, pop = 0, 0
            for cat, nb in val.iteritems():
                cat_varname = var + '_' + str(cat)
                data[cat_varname] = dummies_dict[cat]
                margins_new[cat_varname] = nb
                if var not in margins_new_dict:
                    margins_new_dict[var] = {}
                margins_new_dict[var][cat] = nb
                pop += nb
                k += 1
                nj += 1
            # Check total popualtion
            if pop != total_population:
                if use_proportions:
                    log.info(
                        'calmar: categorical variable {} is inconsistent with population; using proportions'.format(
                            var
                            )
                        )
                    for cat, nb in val.iteritems():
                        cat_varname = var + '_' + str(cat)
                        margins_new[cat_varname] = nb * total_population / pop
                        margins_new_dict[var][cat] = nb * total_population / pop
                else:
                    raise Exception('calmar: categorical variable ', var, ' is inconsistent with population')
        else:
            margins_new[var] = val
            margins_new_dict[var] = val
            nj += 1

    # On conserve systematiquement la population
    if hasattr(data, 'dummy_is_in_pop'):
        raise Exception('dummy_is_in_pop is not a valid variable name')

    data['dummy_is_in_pop'] = ones(nk)
    margins_new['dummy_is_in_pop'] = total_population

    # paramètres de Lagrange initialisés à zéro
    lambda0 = zeros(nj)

    # initial weights
    d = data[pondini]
    x = zeros((nk, nj))  # nb obs x nb constraints
    xmargins = zeros(nj)
    margins_dict = {}
    j = 0
    for var, val in margins_new.iteritems():
        x[:, j] = data[var]
        xmargins[j] = val
        margins_dict[var] = val
        j += 1

    # Résolution des équations du premier ordre
    def constraint(l):
        return dot(d * F(dot(x, l)), x) - xmargins

    def constraint_prime(l):
        return dot(d * (x.T * F_prime(dot(x, l))), x)
    # le jacobien celui ci-dessus est constraintprime = @(l) x*(d.*Fprime(x'*l)*x');

    tries, ier = 0, 2
    if 'xtol' in parameters:
        xtol = parameters['xtol']
    else:
        xtol = 1.49012e-08

    err_max = 1
    conv = 1
    while (ier == 2 or ier == 5 or ier == 4) and not (tries >= 10 or (err_max < 1e-6 and conv < 1e-8)):
        lambdasol, infodict, ier, mesg = fsolve(
            constraint,
            lambda0,
            fprime = constraint_prime,
            maxfev = 256,
            xtol = xtol,
            full_output = 1)
        lambda0 = 1 * lambdasol
        tries += 1

        pondfin = d * F(dot(x, lambdasol))
        rel_error = {}
        for var, val in margins_new.iteritems():
            rel_error[var] = abs((data[var] * pondfin).sum() - margins_dict[var]) / margins_dict[var]
        sorted_err = sorted(rel_error.iteritems(), key = operator.itemgetter(1), reverse = True)

        conv = abs(err_max - sorted_err[0][1])
        err_max = sorted_err[0][1]

    if (ier == 2 or ier == 5 or ier == 4):
        log.info("calmar: stopped after {} tries".format(tries))
    # rebuilding a weight vector with the same size of the initial one
    pondfin_out = array(data_in[pondini], dtype = float64)
    pondfin_out[is_weight_not_null] = pondfin
    return pondfin_out, lambdasol, margins_new_dict


def check_calmar(data_in, margins, pondini='wprm_init', pondfin_out = None, lambdasol = None, margins_new_dict = None):
    for variable, margin in margins.iteritems():
        if variable != 'total_population':
            print variable, margin, abs(margin - margins_new_dict[variable]) / abs(margin)
