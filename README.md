# OpenFisca Core

[OpenFisca](http://openfisca.org/doc/) is a versatile microsimulation free software. Check the [online documentation](http://openfisca.org/doc/) for more details.

This package contains the core features of OpenFisca, which are meant to be used by country packages such as [OpenFisca-France](https://github.com/openfisca/openfisca-france). Bootstrapping your own country package should not take more than 5 minutes: check our [country package template](https://github.com/openfisca/country-template).

## Environment

This package requires Python 2.7

## Installation

If you're developping your own country package, you don't need to explicitly install OpenFisca-Core. It just needs to appear [in your package dependencies](https://github.com/openfisca/openfisca-france/blob/18.2.1/setup.py#L53).

If you want to contribute to OpenFisca-Core itself, welcome! To install it locally in development mode:

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

### Tracker

The OpenFisca Web API comes with an [optional tracker](https://github.com/openfisca/tracker) which allows you to measure the usage of the API.

#### Tracker installation

The tracker is not installed by default. To install it, run:

```sh
pip install openfisca_core[tracker]  # Or `pip install --editable ".[tracker]"` for an editable installation
```


#### Tracker configuration

The tracker is activated when these two environment variables are set:

* `TRACKER_URL`: An URL ending with `piwik.php`. It defines the Piwik instance that will receive the tracking information. To use the main OpenFisca Piwik instance, use `https://stats.data.gouv.fr/piwik.php`.
* `TRACKER_IDSITE`: An integer. It defines the identifier of the tracked site on your Piwik instance. To use the main OpenFisca piwik instance, use `4`.

For instance, to run the Web API with the mock country package `openfisca_country_template` and the tracker activated, run:

```sh
COUNTRY_PACKAGE=openfisca_country_template TRACKER_URL="https://stats.data.gouv.fr/piwik.php" TRACKER_IDSITE=4 gunicorn "openfisca_web_api_preview.app:create_app()" --bind localhost:5000 --workers 3
```
