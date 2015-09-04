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
