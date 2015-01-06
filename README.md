# OpenFisca

## Presentation

OpenFisca is a versatile microsimulation free software.

It is designed to microsimulate the tax-benefit system of any country.

See [France](https://github.com/openfisca/openfisca-france) and [Tunisia](https://github.com/openfisca/openfisca-tunisia) countries.

The [web user interface](https://github.com/openfisca/openfisca-web-ui) allows the user to compute and display all these taxes and benefits for any type of household.

The impact of any modification in the legislation can also be computed via reforms.

When plugged on a survey, OpenFisca can also compute the budgetary consequences
of a reform and its distributional impact.

The current version implements a large set of taxes, social benefits
and housing provision for [France](https://github.com/openfisca/openfisca-france) for the last 10 years.

Please consult http://www.openfisca.fr/presentation for more information.

## Documentation

Please consult http://www.openfisca.fr/documentation

## Install

This section explains how to install the OpenFisca-Core part of the OpenFisca project. Please consult the more general [OpenFisca installation documentation](http://www.openfisca.fr/installation) if you want to install the whole OpenFisca project.

Clone the OpenFisca-Core Git repository on your machine:

```
git clone https://github.com/openfisca/openfisca-core.git
cd openfisca-core
python setup.py compile_catalog
pip install -e . --user
```

These instructions suggest the `--user` option of `pip` but you can also use a Python `virtualenv`.

Now you should import the openfisca_core module in a Python shell without any error:

```
python
>>> import openfisca_core
>>> openfisca_core
<module 'openfisca_core' from 'openfisca_core/__init__.pyc'>
```

## Contribute

OpenFisca is a [FLOSS](http://en.wikipedia.org/wiki/Free_and_open-source_software#FLOSS) project. Its source code is distributed
under the GNU Affero General Public Licence version 3 or later (see COPYING).

Feel free to join the OpenFisca development team on GitHub
(https://github.com/openfisca) or contact us by email at
contact@openfisca.fr
