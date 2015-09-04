# OpenFisca Core

[![Build Status](https://travis-ci.org/openfisca/openfisca-core.svg?branch=master)](https://travis-ci.org/openfisca/openfisca-core)

[More build status](http://www.openfisca.fr/build-status)

## Presentation

[OpenFisca](http://www.openfisca.fr/) is a versatile microsimulation free software.
This is the source code of the Core module.

Please consult http://www.openfisca.fr/presentation

## Documentation

Please consult http://www.openfisca.fr/documentation

## See also

* [reforms](docs/reforms.md)
* [GNU/Linux Debian / Ubuntu](docs/gnu-linux-debian.md)
* [Microsoft Windows](docs/microsoft-windows.md)

## Installation

> GNU/Linux Debian users should read this dedicated doc: [GNU/Linux Debian / Ubuntu](docs/gnu-linux-debian.md).

> Microsoft Windows users should read this dedicated doc: [Microsoft Windows](docs/microsoft-windows.md).

Requirements:

* [Git](http://www.git-scm.com/)
* [Python](http://www.python.org/) 2.7
* numpy and scipy, scientific computing packages for Python.
Since they are developed in C you should install them pre-compiled for your operating system.

Clone the OpenFisca-Core Git repository on your machine and install the Python package.

Assuming you are in an `openfisca` working directory:


```
git clone https://github.com/openfisca/openfisca-core.git
cd openfisca-core
git checkout next
pip install --editable . --user # Microsoft Windows users must not use the `--user` option
python setup.py compile_catalog
```

Once OpenFisca-Core is installed, the next step is to install the a tax and benefit system.
Choose one of:

- [OpenFisca-France](https://github.com/openfisca/openfisca-france)
- [OpenFisca-Tunisia](https://github.com/openfisca/openfisca-tunisia)

## Contribute

OpenFisca is a free software project.
Its source code is distributed under the [GNU Affero General Public Licence](http://www.gnu.org/licenses/agpl.html)
version 3 or later (see COPYING).

Feel free to join the OpenFisca development team on [GitHub](https://github.com/openfisca) or contact us by email at
contact@openfisca.fr
