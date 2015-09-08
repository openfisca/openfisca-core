# Tests

OpenFisca has three sorts of tests:

* unit tests
* test-case tests
* scenario tests

## ipdb debugger

If a test fails, you can execute it with the [debug](http://nose.readthedocs.org/en/latest/plugins/debug.html) nose plugin:

    nosetests --pdb openfisca_core/tests/test_tax_scales.py

You can even [specify the exact test to launch](http://nose.readthedocs.org/en/latest/usage.html#selecting-tests):

    nosetests --pdb openfisca_core/tests/test_tax_scales.py:test_linear_average_rate_tax_scale

> The [nose-ipdb](https://github.com/flavioamieiro/nose-ipdb/) plugin is more user-friendly since it uses the [ipdb](https://github.com/gotcha/ipdb) debugger which uses the [ipython](http://ipython.org/) interactive shell.

> In this case, just use the `--ipdb` option rather than `--pdb`.

## Travis automated tests platform

OpenFisca uses [Travis CI](https://travis-ci.org/openfisca) to run tests automatically after each `git push`.

The git branches used during development are `master` and `next`.

The repositories tested by Travis are:

* [OpenFisca-Core](https://github.com/openfisca/openfisca-core)
* [OpenFisca-France](https://github.com/openfisca/openfisca-france)
* [OpenFisca-Web-UI](https://github.com/openfisca/openfisca-web-ui)
* [OpenFisca-Web-API](https://github.com/openfisca/openfisca-web-api)

The goal is to ensure that:
* each repository in the `master` branch state works well with all the others in the `master` branch state
* each repository in the `next` branch state works well with all the others in the `next` branch state
* each repository in a release tag state works well with all the others dependent repositories in the required versions tags

The OpenFisca website hosts a summary page: http://www.openfisca.fr/build-status
