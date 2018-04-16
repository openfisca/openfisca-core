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

To run the entire test suite:

```sh
make test
```

To run all the tests defined on a test file:

```sh
nosetests core/test_parameters.py
```

To run a single test:

```sh
nosetests core/test_parameters.py:test_parameter_for_period
```

## Serving the API

OpenFisca-Core provides a Web-API. It is served on the `6000` port.

To run it with the mock country package `openfisca_country_template` and another port value as `5000`, run:

```sh
openfisca serve --country-package openfisca_country_template --port 5000
```

To read more about the `openfisca serve` command, check out its [documentation](https://openfisca.readthedocs.io/en/latest/openfisca_serve.html).

By default, the Web API uses 3 workers to avoid [this issue](http://stackoverflow.com/questions/11150343/slow-requests-on-local-flask-server). Without it, AJAX requests from Chrome sometimes take more than 20s to process. You can change the number of workers by specifying a `--workers k` option.

You can test that the API is running by executing the command:

```sh
curl http://localhost:5000/parameters
```
For more information about endpoints and input formatting, see the [official documentation](http://openfisca.org/doc/openfisca-web-api).

### Tracker

The OpenFisca Web API comes with an [optional tracker](https://github.com/openfisca/tracker) which allows you to measure the usage of the API.

#### Tracker installation

The tracker is not installed by default. To install it, run:

```sh
pip install openfisca_core[tracker]  # Or `pip install --editable ".[tracker]"` for an editable installation
```


#### Tracker configuration

The tracker is activated when these two options are set:

* `--tracker-url`: An URL ending with `piwik.php`. It defines the Piwik instance that will receive the tracking information. To use the main OpenFisca Piwik instance, use `https://stats.data.gouv.fr/piwik.php`.
* `--tracker-idsite`: An integer. It defines the identifier of the tracked site on your Piwik instance. To use the main OpenFisca piwik instance, use `4`.
* `--tracker-token`: A string. It defines the Piwik API Authentification token to differentiate API calls based on the user IP. Otherwise, all API calls will seem to come from your server. The Piwik API Authentification token can be found in your Piwik interface, when you are logged.

For instance, to run the Web API with the mock country package `openfisca_country_template` and the tracker activated, run:

```sh
openfisca serve --country-package openfisca_country_template --port 5000 --tracker-url https://stats.data.gouv.fr/piwik.php --tracker-idsite 4 --tracker-token $TRACKER_TOKEN
```
