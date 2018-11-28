# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import

import os

import dpath

from openfisca_core.commons import to_unicode


class VariableNotFound(Exception):
    """
        Exception raised when a variable has been queried but is not defined in the TaxBenefitSystem.
    """

    def __init__(self, variable_name, tax_benefit_system):
        """
        :param variable_name: Name of the variable that was queried.
        :param tax_benefit_system: Tax benefits system that does not contain `variable_name`
        """
        country_package_metadata = tax_benefit_system.get_package_metadata()
        country_package_name = country_package_metadata['name']
        country_package_version = country_package_metadata['version']
        if country_package_version:
            country_package_id = '{}@{}'.format(country_package_name, country_package_version)
        else:
            country_package_id = country_package_name
        message = os.linesep.join([
            "You tried to calculate or to set a value for variable '{0}', but it was not found in the loaded tax and benefit system ({1}).".format(variable_name, country_package_id),
            "Are you sure you spelled '{0}' correctly?".format(variable_name),
            "If this code used to work and suddenly does not, this is most probably linked to an update of the tax and benefit system.",
            "Look at its changelog to learn about renames and removals and update your code. If it is an official package,",
            "it is probably available on <https://github.com/openfisca/{0}/blob/master/CHANGELOG.md>.".format(country_package_name)
            ])
        self.message = message
        Exception.__init__(self, self.message.encode('utf-8'))


class SituationParsingError(Exception):
    """
        Exception raised when the situation provided as an input for a simulation cannot be parsed
    """

    def __init__(self, path, message, code = None):
        self.error = {}
        dpath_path = '/'.join([str(item) for item in path])
        message = to_unicode(message)
        message = message.strip(os.linesep).replace(os.linesep, ' ')
        dpath.util.new(self.error, dpath_path, message)
        self.code = code
        Exception.__init__(self, str(self.error).encode('utf-8'))

    def __str__(self):
        return str(self.error)


class PeriodMismatchError(ValueError):
    """
        Exception raised when one tries to set a variable value for a period that doesn't match its definition period
    """

    def __init__(self, variable_name, period, definition_period, message):
        self.variable_name = variable_name
        self.period = period
        self.definition_period = definition_period
        self.message = message
        ValueError.__init__(self, self.message)
