# -*- coding: utf-8 -*-

from nose.tools import assert_equal
from . import distribution, subject

parameters_response = subject.get('/parameters')


def test_package_name_header():
    assert_equal(parameters_response.headers.get('Country-Package'), distribution.key)


def test_package_version_header():
    assert_equal(parameters_response.headers.get('Country-Package-Version'), distribution.version)
