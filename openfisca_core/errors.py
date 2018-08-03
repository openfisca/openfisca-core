# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
from os import linesep


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
        message = linesep.join([
            "You tried to calculate or to set a value for variable '{0}', but it was not found in the loaded tax and benefit system ({1}).".format(variable_name, country_package_id),
            "Are you sure you spelled '{0}' correctly?".format(variable_name),
            "If this code used to work and suddenly does not, this is most probably linked to an update of the tax and benefit system.",
            "Look at its changelog to learn about renames and removals and update your code. If it is an official package,",
            "it is probably available on <https://github.com/openfisca/{0}/blob/master/CHANGELOG.md>.".format(country_package_name)
            ])
        self.message = message
        Exception.__init__(self, self.message.encode('utf-8'))
