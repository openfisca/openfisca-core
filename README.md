# OpenFisca Core

[![Build Status](https://travis-ci.org/openfisca/openfisca-core.svg?branch=master)](https://travis-ci.org/openfisca/openfisca-core)

[More build statuses](https://www.openfisca.fr/build-status)

[OpenFisca](https://www.openfisca.fr/) is a versatile microsimulation free software.
This is the source code of the Core module.

The documentation of the project is hosted at https://doc.openfisca.fr/

## Install for development

This is the way to install OpenFisca-Core for development. If you just want to modify the legislation formulas and/or parameters, just follow the [installation section](https://doc.openfisca.fr/install.html) of the documentation.

This package requires Python 2.7.

```bash
git clone https://github.com/openfisca/openfisca-core.git
cd openfisca-core
pip install --editable .
python setup.py compile_catalog
```
