# OpenFisca Core

[![Build Status](https://travis-ci.org/openfisca/openfisca-core.svg?branch=master)](https://travis-ci.org/openfisca/openfisca-core)

[More build statuses](http://www.openfisca.fr/build-status)

[OpenFisca](http://www.openfisca.fr/) is a versatile microsimulation free software.
This is the source code of the Core module.

The documentation of the project is hosted at http://doc.openfisca.fr/

## Install for development

This is the way to install OpenFisca-Core for development. If you just want to modify the legislation formulas and/or parameters,
just follow the [installation section](http://doc.openfisca.fr/en/install.html) of the documentation.

> We recommend using Miniconda because it's the simplest solution we've found to install Python scientific packages like NumPy for the different operating systems.

> Start by following their [quick install page](http://conda.pydata.org/docs/install/quick.html).

```
git clone https://github.com/openfisca/openfisca-core.git
cd openfisca-core
pip install --editable .
python setup.py compile_catalog
```
