# OpenFisca Core

[OpenFisca](https://doc.openfisca.fr/) is a versatile microsimulation free software. Check the [online documentation](https://doc.openfisca.fr/) for more details.

This package contains the core features of OpenFisca, which are meant to be used by country packages such as [OpenFisca-France](https://github.com/openfisca/openfisca-france). Bootstrapping your own country package should not take more than 5 minutes: check our [country package template](https://github.com/openfisca/country-template).

## Environment

This package requires Python 2.7

## Installation

If you're developping your own country package, you don't need to explicitly install OpenFisca-Core. It just needs to appear [in your package dependencies](https://github.com/openfisca/openfisca-france/blob/18.2.1/setup.py#L53).

If you want to contribute to OpenFisca-Core itself, welcome! To install it locally in developpment mode:

```bash
git clone https://github.com/openfisca/openfisca-core.git
cd openfisca-core
pip install --editable ".[test]"
```

## Testing

```sh
make test
```

## Serving the API

OpenFisca-Core provides a Web-API. To run it with the mock country package `openfisca_country_template`, run:

```sh
COUNTRY_PACKAGE=openfisca_country_template gunicorn "openfisca_web_api_preview.app:create_app()" --bind localhost:5000 --workers 3
```

The `--workers k` (with `k >= 3`) option is necessary to avoid [this issue](http://stackoverflow.com/questions/11150343/slow-requests-on-local-flask-server). Without it, AJAX requests from Chrome sometimes take more than 20s to process.
