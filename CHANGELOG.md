# Changelog

### 42.0.4 [#1257](https://github.com/openfisca/openfisca-core/pull/1257)

#### Technical changes

- Fix conda test and publish
- Add matrix testing to CI
  - Now it tests lower and upper bounds of python and numpy versions

### 42.0.3 [#1234](https://github.com/openfisca/openfisca-core/pull/1234)

#### Technical changes

- Add matrix testing to CI
  - Now it tests lower and upper bounds of python and numpy versions

> Note: Version `42.0.3` has been unpublished as was deployed by mistake.
> Please use versions `42.0.4` and subsequents.

### 42.0.2 [#1256](https://github.com/openfisca/openfisca-core/pull/1256)

#### Documentation

- Fix bad indent

### 42.0.1 [#1253](https://github.com/openfisca/openfisca-core/pull/1253)

#### Documentation

- Fix documentation of `entities`

# 42.0.0 [#1223](https://github.com/openfisca/openfisca-core/pull/1223)

#### Breaking changes

- Changes to `eternity` instants and periods
  - Eternity instants are now `<Instant(-1, -1, -1)>` instead of
    `<Instant(inf, inf, inf)>`
  - Eternity periods are now `<Period(('eternity', <Instant(-1, -1, -1)>, -1))>`
    instead of `<Period(('eternity', <Instant(inf, inf, inf)>, inf))>`
  - The reason is to avoid mixing data types: `inf` is a float, periods and
    instants are integers. Mixed data types make memory optimisations impossible.
  - Migration should be straightforward. If you have a test that checks for
    `inf`, you should update it to check for `-1` or use the `is_eternal` method.
- `periods.instant` no longer returns `None`
  - Now, it raises `periods.InstantError`

#### New features

- Introduce `Instant.eternity()`
  - This behaviour was duplicated across
  - Now it is encapsulated in a single method
- Introduce `Instant.is_eternal` and `Period.is_eternal`
    - These methods check if the instant or period are eternity (`bool`).
- Now `periods.instant` parses also ISO calendar strings (weeks)
  - For instance, `2022-W01` is now a valid input

#### Technical changes

- Update `pendulum`
- Reduce code complexity
- Remove run-time type-checks
- Add typing to the periods module

### 41.5.7 [#1225](https://github.com/openfisca/openfisca-core/pull/1225)

#### Technical changes

- Refactor & test `eval_expression`

###  41.5.6 [#1185](https://github.com/openfisca/openfisca-core/pull/1185)

#### Technical changes

- Remove pre Python 3.9 syntax.

### 41.5.5 [#1220](https://github.com/openfisca/openfisca-core/pull/1220)

#### Technical changes

- Fix doc & type definitions in the entities module

### 41.5.4 [#1219](https://github.com/openfisca/openfisca-core/pull/1219)

#### Technical changes

- Fix doc & type definitions in the commons module

### 41.5.3 [#1218](https://github.com/openfisca/openfisca-core/pull/1218)

#### Technical changes

- Fix `flake8` doc linting:
    - Add format "google"
    - Fix per-file skips
- Fix failing lints

### 41.5.2 [#1217](https://github.com/openfisca/openfisca-core/pull/1217)

#### Technical changes

- Fix styles by applying `isort`.
- Add a `isort` dry-run check to `make lint`

### 41.5.1 [#1216](https://github.com/openfisca/openfisca-core/pull/1216)

#### Technical changes

- Fix styles by applying `black`.
- Add a `black` dry-run check to `make lint`

## 41.5.0 [#1212](https://github.com/openfisca/openfisca-core/pull/1212)

#### New features

- Introduce `VectorialAsofDateParameterNodeAtInstant`
  - It is a parameter node of the legislation at a given instant which has been vectorized along some date.
   - Vectorized parameters allow requests such as parameters.housing_benefit[date], where date is a `numpy.datetime64` vector

### 41.4.7 [#1211](https://github.com/openfisca/openfisca-core/pull/1211)

#### Technical changes

- Update documentation continuous deployment method to reflect OpenFisca-Doc [process updates](https://github.com/openfisca/openfisca-doc/pull/308)

### 41.4.6 [#1210](https://github.com/openfisca/openfisca-core/pull/1210)

#### Technical changes

- Abide by OpenAPI v3.0.0 instead of v3.1.0
  - Drop support for `propertyNames` in `Values` definition

### 41.4.5 [#1209](https://github.com/openfisca/openfisca-core/pull/1209)

#### Technical changes

- Support loading metadata from both `setup.py` and `pyproject.toml` package description files.

### ~41.4.4~ [#1208](https://github.com/openfisca/openfisca-core/pull/1208)

_Unpublished due to introduced backwards incompatibilities._

#### Technical changes

- Adapt testing pipeline to Country Template [v7](https://github.com/openfisca/country-template/pull/139).

### 41.4.3 [#1206](https://github.com/openfisca/openfisca-core/pull/1206)

#### Technical changes

- Increase spiral and cycle tests robustness.
  - The current test is ambiguous, as it hides a failure at the first spiral
    occurrence (from 2017 to 2016).

### 41.4.2 [#1203](https://github.com/openfisca/openfisca-core/pull/1203)

#### Technical changes

- Changes the Pypi's deployment authentication way to use token API following Pypi's 2FA enforcement starting 2024/01/01.

### 41.4.1 [#1202](https://github.com/openfisca/openfisca-core/pull/1202)

#### Technical changes

- Check that entities are fully specified when expanding over axes.

## 41.4.0 [#1197](https://github.com/openfisca/openfisca-core/pull/1197)

#### New features

- Add `entities.find_role()` to find roles by key and `max`.

#### Technical changes

- Document `projectors.get_projector_from_shortcut()`.

## 41.3.0 [#1200](https://github.com/openfisca/openfisca-core/pull/1200)

> As `TracingParameterNodeAtInstant` is a wrapper for `ParameterNodeAtInstant`
> which allows iteration and the use of `contains`, it was not possible
> to use those on a `TracingParameterNodeAtInstant`

#### New features

- Allows iterations on `TracingParameterNodeAtInstant`
- Allows keyword `contains` on `TracingParameterNodeAtInstant`

## 41.2.0 [#1199](https://github.com/openfisca/openfisca-core/pull/1199)

#### Technical changes

- Fix `openfisca-core` Web API error triggered by `Gunicorn` < 22.0.
  - Bump `Gunicorn` major revision to fix error on Web API.
    Source: https://github.com/benoitc/gunicorn/issues/2564

### 41.1.2 [#1192](https://github.com/openfisca/openfisca-core/pull/1192)

#### Technical changes

- Add tests to `entities`.

###  41.1.1 [#1186](https://github.com/openfisca/openfisca-core/pull/1186)

#### Technical changes

- Skip type-checking tasks
  - Before their definition was commented out but still run with `make test`
  - Now they're skipped but not commented, which is needed to fix the
    underlying issues

##  41.1.0 [#1195](https://github.com/openfisca/openfisca-core/pull/1195)

#### Technical changes

- Make `Role` explicitly hashable.
- Details:
    - By introducing `__eq__`, naturally `Role` became unhashable, because
      equality was calculated based on a property of `Role`
      (`role.key == another_role.key`), and no longer structurally
      (`"1" == "1"`).
    - This changeset removes `__eq__`, as `Role` is being used downstream as a
      hashable object, and adds a test to ensure `Role`'s hashability.

###  41.0.2 [#1194](https://github.com/openfisca/openfisca-core/pull/1194)

#### Technical changes

- Add `__hash__` method to `Role`.

###  41.0.1 [#1187](https://github.com/openfisca/openfisca-core/pull/1187)

#### Technical changes

- Document `Role`.

# 41.0.0 [#1189](https://github.com/openfisca/openfisca-core/pull/1189)

#### Breaking changes

- `Variable.get_introspection_data` no longer has parameters nor calling functions

The Web API was very prone to crashing, timeouting at startup because of the time consuming python file parsing to generate documentation displayed for instance in the Legislation Explorer.

##  40.1.0 [#1174](https://github.com/openfisca/openfisca-core/pull/1174)

#### New Features

- Allows for dispatching and dividing inputs over a broader range.
  - For example, divide a monthly variable by week.

###  40.0.1 [#1184](https://github.com/openfisca/openfisca-core/pull/1184)

#### Technical changes

- Require numpy < 1.25 because of memory leak detected in OpenFisca-France.

# 40.0.0 [#1181](https://github.com/openfisca/openfisca-core/pull/1181)

#### Breaking changes

- Upgrade every dependencies to its latest version.
- Upgrade to Python >= 3.9

Note: Checks on mypy typings are disabled, because they cause generate of errors that we were not able to fix easily.

# 39.0.0 [#1181](https://github.com/openfisca/openfisca-core/pull/1181)

#### Breaking changes

- Upgrade every dependencies to their latest versions.
- Upgrade to Python >= 3.9

Main changes, that may require some code changes in country packages:
- numpy
- pytest
- Flask

### 38.0.4 [#1182](https://github.com/openfisca/openfisca-core/pull/1182)

#### Technical changes

- Method `_get_tax_benefit_system()` of class `YamlItem` in file  `openfisca_core/tools/test_runner.py` will now clone the TBS when applying reforms to avoid running tests with previously reformed TBS.

### 38.0.3 [#1179](https://github.com/openfisca/openfisca-core/pull/1179)

#### Bug fix

- Do not install dependencies outside the `setup.py`
  - Dependencies installed outside the `setup.py` are not taken into account by
    `pip`'s dependency resolver.
  - In case of conflicting transient dependencies, the last library installed
    will "impose" its dependency version.
  - This makes the installation and build of the library non-deterministic and
    prone to unforeseen bugs caused by external changes in dependencies'
    versions.

#### Note

A definite way to solve this issue is to clearly separate library dependencies
(with a `virtualenv`) and a universal dependency installer for CI requirements
(like `pipx`), taking care of:

- Always running tests inside the `virtualenv` (for example with `nox`).
- Always building outside of the `virtualenv` (for example with `poetry`
  installed by `pipx`).

Moreover, it is indeed even better to have a lock file for dependencies,
using `pip freeze`) or with tools providing such features (`pipenv`, etc.).

### 38.0.2 [#1178](https://github.com/openfisca/openfisca-core/pull/1178)

#### Technical changes

- Remove use of `importlib_metadata`.

### 38.0.1 -

> Note: Version `38.0.1` has been unpublished as was deployed by mistake.
> Please use versions `38.0.2` and subsequents.


# 38.0.0 [#989](https://github.com/openfisca/openfisca-core/pull/989)

> Note: Version `38.0.0` has been unpublished as `35.11.1` introduced a bug
> preventing users to load a tax-benefit system. Please use versions `38.0.2`
> and subsequents.

#### New Features

- Upgrade OpenAPI specification of the API to v3 from Swagger v2.
- Continuously validate OpenAPI specification.

#### Breaking changes

- Drop support for OpenAPI specification v2 and prior.
  - Users relying on OpenAPI v2 can use [Swagger Converter](https://converter.swagger.io/api/convert?url=OAS2_YAML_OR_JSON_URL) to migrate ([example](https://web.archive.org/web/20221103230822/https://converter.swagger.io/api/convert?url=https://api.demo.openfisca.org/latest/spec)).

### 37.0.2 [#1170](https://github.com/openfisca/openfisca-core/pull/1170)

> Note: Version `37.0.2` has been unpublished as `35.11.1` introduced a bug
> preventing users to load a tax-benefit system. Please use versions `38.0.2`
> and subsequents.

#### Technical changes

- Always import numpy

### 37.0.1 [#1169](https://github.com/openfisca/openfisca-core/pull/1169)

> Note: Version `37.0.1` has been unpublished as `35.11.1` introduced a bug
> preventing users to load a tax-benefit system. Please use versions `38.0.2`
> and subsequents.

#### Technical changes

- Unify casing of NumPy.

# 37.0.0 [#1142](https://github.com/openfisca/openfisca-core/pull/1142)

> Note: Version `37.0.0` has been unpublished as `35.11.1` introduced a bug
> preventing users to load a tax-benefit system. Please use versions `38.0.2`
> and subsequents.

#### Deprecations

- In _periods.Instant_:
  - Remove `period`, method used to build a `Period` from an `Instant`.
  - This method created an upward circular dependency between `Instant` and `Period` causing lots of trouble.
  - The functionality is still provided by `periods.period` and the `Period` constructor.

#### Migration details

- Replace `some_period.start.period` and similar methods with `Period((unit, some_period.start, 1))`.

# 36.0.0 [#1149](https://github.com/openfisca/openfisca-core/pull/1162)

> Note: Version `36.0.0` has been unpublished as `35.11.1` introduced a bug
> preventing users to load a tax-benefit system. Please use versions `38.0.2`
> and subsequents.

#### Breaking changes

- In `ParameterScaleBracket`:
  - Remove the `base` attribute
  - The attribute's usage was unclear and it was only being used by some French social security variables

## 35.12.0 [#1160](https://github.com/openfisca/openfisca-core/pull/1160)

> Note: Version `35.12.0` has been unpublished as `35.11.1` introduced a bug
> preventing users to load a tax-benefit system. Please use versions `38.0.2`
> and subsequents.

#### New Features

- Lighter install by removing test packages from systematic install.

### 35.11.2 [#1166](https://github.com/openfisca/openfisca-core/pull/1166)

> Note: Version `35.11.2` has been unpublished as `35.11.1` introduced a bug
> preventing users to load a tax-benefit system. Please use versions `38.0.2`
> and subsequents.

#### Technical changes

- Fix Holder's doctests.

### 35.11.1 [#1165](https://github.com/openfisca/openfisca-core/pull/1165)

> Note: Version `35.11.1` has been unpublished as it introduced a bug
> preventing users to load a tax-benefit system. Please use versions `38.0.2`
> and subsequents.

#### Bug fix

- Fix documentation
  - Suppression of some modules broke the documentation build

## 35.11.0 [#1149](https://github.com/openfisca/openfisca-core/pull/1149)

#### New Features

- Introduce variable dependent error margins in YAML tests.

### 35.10.1 [#1143](https://github.com/openfisca/openfisca-core/pull/1143)

#### Bug fix

- Reintroduce support for the ``day`` date unit in `holders.set_input_dispatch_by_period` and `holders.
  set_input_divide_by_period`
  - Allows for dispatching values per day, for example, to provide a daily (week, fortnight) to an yearly variable.
  - Inversely, allows for calculating the daily (week, fortnight) value of a yearly input.

## 35.10.0 [#1151](https://github.com/openfisca/openfisca-core/pull/1151)

#### New features

- Add type hints for all instances of `variable_name` in function declarations.
- Add type hints for some `Simulation` and `Population` properties.

## 35.9.0 [#1150](https://github.com/openfisca/openfisca-core/pull/1150)

#### New Features

- Introduce a maximal depth for computation logs
  - Allows for limiting the depth of the computation log chain

### 35.8.6 [#1145](https://github.com/openfisca/openfisca-core/pull/1145)

#### Technical changes

- Removes the automatic documentation build check
  - It has been proven difficult to maintain, specifically due _dependency hell_ and a very contrived build workflow.

### 35.8.5 [#1137](https://github.com/openfisca/openfisca-core/pull/1137)

#### Technical changes

- Fix pylint dependency in fresh editable installations
  - Ignore pytest requirement, used to collect test cases, if it is not yet installed.

### 35.8.4 [#1131](https://github.com/openfisca/openfisca-core/pull/1131)

#### Technical changes

- Correct some type hints and docstrings.

### 35.8.3 [#1127](https://github.com/openfisca/openfisca-core/pull/1127)

#### Technical changes

- Fix the build for Anaconda in CI. The conda build failed on master because of a replacement in a comment string.
  - The _ were removed in the comment to avoid a replace.

### 35.8.2 [#1128](https://github.com/openfisca/openfisca-core/pull/1128)

#### Technical changes

- Remove ambiguous links in docstrings.

### 35.8.1 [#1105](https://github.com/openfisca/openfisca-core/pull/1105)

#### Technical changes

- Add publish to Anaconda in CI. See file .conda/README.md.

## 35.8.0 [#1114](https://github.com/openfisca/openfisca-core/pull/1114)

#### New Features

- Introduce `rate_from_bracket_indice` method on `RateTaxScaleLike` class
  - Allows for the determination of the tax rate based on the tax bracket indice

- Introduce `rate_from_tax_base` method on `RateTaxScaleLike` class
  - Allows for the determination of the tax rate based on the tax base

- Introduce `threshold_from_tax_base` method on `RateTaxScaleLike` class
  - Allows for the determination of the lower threshold based on the tax base

- Add publish openfisca-core library to Anaconda in CI. See file .conda/README.md.

### 35.7.8 [#1086](https://github.com/openfisca/openfisca-core/pull/1086)

#### Technical changes

### 35.7.7 [#1109](https://github.com/openfisca/openfisca-core/pull/1109)

#### Technical changes

- Fix `openfisca-core` Web API error triggered by `Flask` dependencies updates
  - Bump `Flask` patch revision to fix `cannot import name 'json' from 'itsdangerous'` on Web API.
  - Then, fix `MarkupSafe` revision to avoid `cannot import name 'soft_unicode' from 'markupsafe'` error on Web API.

### 35.7.6 [#1065](https://github.com/openfisca/openfisca-core/pull/1065)

#### Technical changes

- Made code compatible with dpath versions >=1.5.0,<3.0.0, instead of >=1.5.0,<2.0.0

### 35.7.5 [#1090](https://github.com/openfisca/openfisca-core/pull/1090)

#### Technical changes

- Remove calls to deprecated imp module

### 35.7.4 [#1083](https://github.com/openfisca/openfisca-core/pull/1083)

#### Technical changes

- Add GitHub `pull-request` event as a trigger to GitHub Actions workflow

### 35.7.3 [#1081](https://github.com/openfisca/openfisca-core/pull/1081)

- Correct error message in case of mis-sized population

### 35.7.2 [#1057](https://github.com/openfisca/openfisca-core/pull/1057)

#### Technical changes

- Switch CI provider from CircleCI to GitHub Actions

### 35.7.1 [#1075](https://github.com/openfisca/openfisca-core/pull/1075)

#### Bug fix

- Fix the collection of OpenFisca-Core tests coverage data
    - Tests within `openfisca_core/*` were not run

## 35.7.0 [#1070](https://github.com/openfisca/openfisca-core/pulls/1070)

#### New Features

- Add group population shortcut to containing groups entities

## 35.6.0 [#1054](https://github.com/openfisca/openfisca-core/pull/1054)

#### New Features

- Introduce `openfisca_core.types`

#### Documentation

- Complete typing of the commons module

#### Dependencies

- `nptyping`
  - To add backport-support for numpy typing
  - Can be removed once lower-bound numpy version is 1.21+

- `typing_extensions`
  - To add backport-support for `typing.Protocol` and `typing.Literal`
  - Can be removed once lower-bound python version is 3.8+

### 35.5.5 [#1055](https://github.com/openfisca/openfisca-core/pull/1055)

#### Documentation

- Complete the documentation of the commons module

### 35.5.4 [#1033](https://github.com/openfisca/openfisca-core/pull/1033)

#### Bug Fixes

- Fix doctests of the commons module

#### Dependencies

- `darglint`, `flake8-docstrings`, & `pylint`
  - For automatic docstring linting & validation.

### 35.5.3 [#1020](https://github.com/openfisca/openfisca-core/pull/1020)

#### Technical changes

- Run openfisca-core & country/extension template tests systematically

### 35.5.2 [#1048](https://github.com/openfisca/openfisca-core/pull/1048)

#### Bug fix

- In _test_yaml.py_:
  - Fix yaml tests loading —required for testing against the built version.

### 35.5.1 [#1046](https://github.com/openfisca/openfisca-core/pull/1046)

#### Non-technical changes

- Reorganise `Makefile` into context files (install, test, publish…)
- Colorise `make` tasks and improve messages printed to the user

## 35.5.0 [#1038](https://github.com/openfisca/openfisca-core/pull/1038)

#### New Features

- Introduce `openfisca_core.variables.typing`
  - Documents the signature of formulas
  - Note: as formulas are generated dynamically, documenting them is tricky

#### Bug Fixes

- Fix the official doc
  - Corrects malformed docstrings
  - Fix missing and/ou outdated references

#### Technical Changes

- Add tasks to automatically validate that changes do not break the documentation

#### Documentation

- Add steps to follow in case the documentation is broken
- Add general documenting guidelines in CONTRIBUTING.md

### 35.4.2 [#1026](https://github.com/openfisca/openfisca-core/pull/1026)

#### Bug fix

- [Web API] Handle a period mismatch error
  - Period mismatch error was not being handled by the API
  - Since it's caused by the user, a 400 (bad request error) is to be expected
  - However, since it was not being handled, a 500 (internal server error) was being given instead

### 35.4.1 [#1007](https://github.com/openfisca/openfisca-core/pull/1007)

#### Bug fix

- Properly check for date validity in parameters.
  - Date validity was being checked only partially, allowing parameters with illegal dates such as "2015-13-32".
  - The changes introduced fix this error and prevent the user when a parameter date is illegal.

## 35.4.0 [#1010](https://github.com/openfisca/openfisca-core/pull/1010)

#### Technical changes

- Update dependencies (_as in 35.3.7_).
  - Extend NumPy compatibility to v1.20 to support M1 processors.

- Make NumPy's type-checking compatible with 1.17.0+
  - NumPy introduced their `typing` module since 1.20.0
  - Previous type hints relying on `annotations` will henceforward no longer work
  - This changes ensure that type hints are always legal for the last four minor NumPy versions

### 35.3.8 [#1014](https://github.com/openfisca/openfisca-core/pull/1014)

#### Bug fix

- Drop latest NumPy supported version to 1.18.x
  - OpenFisca relies on MyPy for optional duck & static type checking
  - When libraries do not implement their own types, MyPy provides stubs, or type sheds
  - Thanks to `__future__.annotations`, those stubs or type sheds are casted to `typing.Any`
  - Since 1.20.x, NumPy now provides their own type definitions
  - The introduction of NumPy 1.20.x in #990 caused one major problem:
    - It is general practice to do not import at runtime modules only used for typing purposes, thanks to the `typing.TYPE_CHEKING` variable
    - The new `numpy.typing` module was being imported at runtime, rendering OpenFisca unusable to all users depending on previous versions of NumPy (1.20.x-)
  - These changes revert #990 and solve #1009 and #1012

### 35.3.7 [#990](https://github.com/openfisca/openfisca-core/pull/990)

_Note: this version has been unpublished due to an issue introduced by NumPy upgrade. Please use 34.3.8 or a more recent version._

#### Technical changes

- Update dependencies.
  - Extend NumPy compatibility to v1.20 to support M1 processors.

### 35.3.6 [#984](https://github.com/openfisca/openfisca-core/pull/984)

#### Technical changes

- In web_api tests, extract `test_client` to a fixture reusable by all the tests in the test suite.
  - To mitigate possible performance issues, by default the fixture is initialised once per test module.
  - This follows the same approach as [#997](https://github.com/openfisca/openfisca-core/pull/997)


### 35.3.5 [#997](https://github.com/openfisca/openfisca-core/pull/997)

#### Technical changes

- In tests, extract `CountryTaxBenefitSystem` to a fixture reusable by all the tests in the test suite.
  - It allows for a better reusability of test scenarios available to new contributors.
  - To mitigate possible performance issues, by default the fixture is initialised once per test module.

### 35.3.4 [#999](https://github.com/openfisca/openfisca-core/pull/999)

#### Technical improvements

- Change logging.warning to warnings.warn to allow users of the package to hide them.

### 35.3.3 [#994](https://github.com/openfisca/openfisca-core/pull/994)

#### Bug fix

- Repair expansion of axes on a variable given as input
  - When expanding axes, the expected behavour is to override any input value for the requested variable and period
  - As longs as we passed some input for a variable on a period, it was not being overrode, creating a NumPy's error (boradcasting)
  - By additionally checking that an input was given, now we make that the array has the correct shape by constructing it with NumPy's tile with a shape equal to the number of the axis expansion count requested.

### 35.3.2 [#992](https://github.com/openfisca/openfisca-core/pull/992)

#### Technical improvements

- Render all OpenFisca Core components modular and sandboxed
  - Allows for simpler contribution
  - Allows for better unit testing
  - Allows for dealing with circular dependencies
  - Allows for more explicit contracts between components

#### Future deprecations

- Reorganise `formula_helpers`, `memory_config`, `rates`, `simulation_builder`.
  - Their functionalities are still there, just moved around
  - Transitional `__init__.py` files added to make transition smooth

- Rename of some errors for consistency
  - Added the suffix `Error` to all errors
  - They're still exposed publicly as they were before

### 35.3.1 [#993](https://github.com/openfisca/openfisca-core/pull/993)

#### Bug fix

- [Web API] Gracefully handle unexpected errors
  - The exception signature expected by the internal server error handler was not the good one
  - Henceforth no response was being given to the user, when a 500 with an explanation was expected

## 35.3.0 [#985](https://github.com/openfisca/openfisca-core/pull/985)

#### New features

- Introduce max_spiral_loops option in YAML test files
  - Allows for control of spiral depth for every test

## 35.2.0 [#982](https://github.com/openfisca/openfisca-core/pull/982)

#### Technical changes

- Allow parameters to be arrays.

### 35.1.1 [#981](https://github.com/openfisca/openfisca-core/pull/981)

#### Technical changes

- Fix false negative web API test following an update in the country template used for testing.

## 35.1.0 [#973](https://github.com/openfisca/openfisca-core/pull/973)

#### Technical changes

- Extend assert_near so it is able to compare dates.

### 35.0.5 [#974](https://github.com/openfisca/openfisca-core/pull/974)

#### Technical changes

- Fix web api test for a parameter node request with `/parameter` endpoint.
- Details:
  - Untie the test from `OpenFisca-Country-Template` parameters list.

### 35.0.4 [#965](https://github.com/openfisca/openfisca-core/pull/965)

#### Technical changes

- Improve error message when laoding parameters file to detect the problematic file

### 35.0.3 [#961](https://github.com/openfisca/openfisca-core/pull/961)

#### Technical changes

- Merge `flake8` and `pep8` configurations as they are redundant.
- Details:
  - Use `flake8` configuration for `flake8` and `autopep8` dependencies.

### 35.0.2 [#967](https://github.com/openfisca/openfisca-core/pull/967)

#### Technical changes

- Update dependency: `flask-cors` (`Flask` extension for Cross Origin Resouce Sharing)

### 35.0.1 [#968](https://github.com/openfisca/openfisca-core/pull/968)

#### Technical changes

- Fix a bug when using axes with an integer year period
  - Always index periods by their string representation in the memory of known input values of a simulation

# 35.0.0 [#954](https://github.com/openfisca/openfisca-core/pull/954)

#### Breaking changes

- Update NumPy version's upper bound to 1.18
  - NumPy 1.18 [expires a list of old deprecations](https://numpy.org/devdocs/release/1.18.0-notes.html#expired-deprecations) that might be used in openfisca country models.

#### Migration details

You might need to change your code if any of the [NumPy expired deprecations](https://numpy.org/devdocs/release/1.18.0-notes.html#expired-deprecations) is used in your model formulas.

Here is a subset of the deprecations that you might find in your model with some checks and migration steps (where `np` stands for `numpy`):

* `Removed deprecated support for boolean and empty condition lists in numpy.select.`
  * Before `numpy.select([], [])` result was `0` (for a `default` argument value set to `0`).
    * Now, we have to check for empty conditions and, return `0` or the defined default argument value when we want to keep the same behavior.
  * Before, integer conditions where transformed to booleans.
    * For example, `numpy.select([0, 1, 0], ['a', 'b', 'c'])` result was `array('b', dtype='<U21')`. Now, we have to update such code to: `numpy.select(numpy.array([0, 1, 0]).astype(bool), ['a', 'b', 'c'])`.
* `numpy.linspace parameter num must be an integer.`
  * No surprise here, update the `num` parameter in [numpy.linspace](https://numpy.org/doc/1.18/reference/generated/numpy.linspace.html) in order to get an integer.
* `Array order only accepts ‘C’, ‘F’, ‘A’, and ‘K’.`
  * Check that [numpy.array](https://numpy.org/doc/1.18/reference/generated/numpy.array.html) `order` argument gets one of the allowed values listed above.
* `UFuncs with multiple outputs must use a tuple for the out kwarg.`
  * Update the output type of any used [universal function](https://numpy.org/doc/1.18/reference/ufuncs.html) to get a tuple.

### 34.7.7 [#951](https://github.com/openfisca/openfisca-core/pull/951)

#### Technical changes

- Avoid Web API failure with _dynamic_ variable generation
- Using reforms to create _dynamic_ variables can lead to a failure to start the API because introspection is failing to get a `source code` section

### 34.7.6 [#957](https://github.com/openfisca/openfisca-core/pull/957)

#### Technical changes

- Update dependencies: `sortedcontainers`

### 34.7.5 [#958](https://github.com/openfisca/openfisca-core/pull/958)

#### Technical changes

- Fix `PytestDeprecationWarning` on `openfisca test` command

### 34.7.4 [#955](https://github.com/openfisca/openfisca-core/pull/955)

#### Technical changes

- Update dependencies: flake8 (style consistency enforcement)

### 34.7.3 [#953](https://github.com/openfisca/openfisca-core/pull/953)

#### Technical changes

- Update dependencies: flask

### 34.7.2 [#948](https://github.com/openfisca/openfisca-core/pull/948)

#### Technical changes

- Revert `dpath` dependency bump introduced by [#940](https://github.com/openfisca/openfisca-core/pull/940)
  - Fix bug in period interpretation by Web API ([openfisca-france#1413](https://github.com/openfisca/openfisca-france/issues/1413))

### 34.7.1 [#940](https://github.com/openfisca/openfisca-core/pull/940)

_Note: this version has been unpublished due to an issue introduced by dpath upgrade. Please use 34.7.2 or a more recent version._

#### Technical changes

- Update dependencies: dpath, autopep8

## 34.7.0 [#943](https://github.com/openfisca/openfisca-core/pull/943)

#### Deprecations

- Deprecate `Dummy`.
  - The functionality is now directly provided by `empty_clone`.

#### Technical changes

- Refactor abstract scales to use Python's `abc` lib.
  - This allows for consistent inheritance, which wasn't the case before.

### 34.6.11 [#945](https://github.com/openfisca/openfisca-core/pull/945)

#### Technical changes

- Fixes web api loading to match latest `Werkzeug` dependency revision (`1.0.0`)
- Details:
  - Preserve not merging double slashes by default.
  - Update `ProxyFix` module loading and initialising arguments.

### 34.6.10 [#946](https://github.com/openfisca/openfisca-core/pull/946)

#### Technical changes

- Fix `Werkzeug` library version
  - Temporarily fix Web API loading disturbed by some `Werkzeug` deprecations

### 34.6.9 [#925](https://github.com/openfisca/openfisca-core/pull/925)

#### Documentation

- Annotates the expected type of the axis count in `SimulationBuilder`.

### 34.6.8 [#936](https://github.com/openfisca/openfisca-core/pull/936)

#### Technical change

- Update dependency: numexpr

### 34.6.7 [#932](https://github.com/openfisca/openfisca-core/pull/932)

#### Documentation

- Add typing to `indexed_enums.py`.
- Details:
  - Type-annotate `ndarray` types to help contributors know the actual methods signatures.

### 34.6.6 [#931](https://github.com/openfisca/openfisca-core/pull/931)

#### Technical changes

- Improve `indexed_enums.py` code style.
  - Remove useless encoding declaration.
  - Use more explicit imports.
  - Improve indentation.
  - Use f-style string interpolation.

### 34.6.5 [#930](https://github.com/openfisca/openfisca-core/pull/930)

#### Documentation

- Improve `indexed_enums.py` documentation.
  - Reduce line length.
  - Fix code examples.
  - Fix indentation.

### 34.6.4 [#929](https://github.com/openfisca/openfisca-core/pull/929)

#### Documentation

- Add more explicit typing annotations for `ndarrays`.

### 34.6.3 [#928](https://github.com/openfisca/openfisca-core/pull/928)

#### Technical changes

- Use `asarray` in `taxscales.py` when we know the argument is a `ndarray`.
- Details:
  - It prevents `numpy` to copy the array if the `dtype` is compatible.

### 34.6.2 [#927](https://github.com/openfisca/openfisca-core/pull/927)

#### Documentation

- Improve `taxscales.py` documentation.
- Details:
  - Specify the types of the arguments.
  - Follow the same style as other parts of the documentation.

### 34.6.1 [#926](https://github.com/openfisca/openfisca-core/pull/926)

#### Technical change

- Downgrade numpy version's upper bound to 1.17
- Details:
  - NumPy 1.18 deprecates the use of several of its methods.
  - Changes in `numpy.select` have impacted other packages depending on OpenFisca Core.

## 34.6.0 [#920](https://github.com/openfisca/openfisca-core/pull/920)

_Note: this version has been unpublished due to an issue introduced by 34.5.4. Please use 34.6.1 or a more recent version._

#### New features

- Introduce `AbstractTaxRateScale.bracket_indices`.
- Introduce `MarginalTaxScale.marginal_rates`.
- Details:
  - This new methods allow users to:
    - Compute the bracket indices relevant for any tax base.
    - Compute the marginal rates relevant for any tax base.

#### Usage notes

1. To use `AbstractTaxRateScale.bracket_indices`:

    ```py
    from numpy import array

    from openfisca_core.taxscales import AbstractRateTaxScale

    tax_scale = AbstractRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(100, 0.1)
    tax_base = array([0, 150])
    tax_scale.bracket_indices(tax_base)  # [0, 1]
    ```

2. To use `MarginalTaxScale.marginal_rates`:

    ```py
    from numpy import array

    from openfisca_core.taxscales import MarginalRateTaxScale

    tax_scale = MarginalRateTaxScale()
    tax_scale.add_bracket(0, 0)
    tax_scale.add_bracket(100, 0.1)
    tax_base = array([0, 150])
    tax_scale.marginal_rates(tax_base)  # [0.0, 0.1]
    ```

### 34.5.4 [#919](https://github.com/openfisca/openfisca-core/pull/919)

#### Technical change

_Note: this version has been unpublished due to an issue introduced by it. Please use 34.6.1 or a more recent version._

- Update numpy version's upper bound to 1.18

### 34.5.3 [#915](https://github.com/openfisca/openfisca-core/pull/915)

- Rename deprecated doc reference `openfisca-run-test` to `openfisca_test`.

### 34.5.2 [#914](https://github.com/openfisca/openfisca-core/pull/914)

- Refactor the use of the now-deprecated `gunicorn.six` module.
  - In versions < 20, [gunicorn](http://docs.gunicorn.org/en/19.3/custom.html) provided the `gunicorn.six` module.
  - In version >= 20, this [gunicorn](http://docs.gunicorn.org/en/stable/custom.html) module has been deprecated.
  - Adapt `openfisca serve` code to the new gunicorn API.

### 34.5.1 [#911](https://github.com/openfisca/openfisca-core/pull/911)

- Remove the library `enum34` from requirements
  - The library `enum34` provides a backport of >= 3.4 `enum` to >= 2.7, < 3.4 Python environments.
  - The standard `enum` and `enum34` are hence incompatible as installed under the same path.
  - Since we dropped support for <= 3.6, that library is no longer needed.

## 34.5.0 [#909](https://github.com/openfisca/openfisca-core/pull/909)

- Introduce `tax_benefit_system.annualize_variable(variable_name, period)` method
  - Used in reform, this method allows to speed up variable calculations when a month-to-month calculation is not relevant, for instance if the input data are annual.

### 34.4.5 [#906](https://github.com/openfisca/openfisca-core/pull/906)

- Make the tracer generate CSV tables containing details about calculation times
- Make `tracer.get_flat_trace` scale for large populations

### 34.4.4 [#908](https://github.com/openfisca/openfisca-core/pull/908)

- Make parameter cloning return clones that are truly independant from their source
  - Before this PR, editing the clone of a parameter tree would change the initial tree
  - Only impacts reforms that edit parameters tree

### 34.4.3 [#907](https://github.com/openfisca/openfisca-core/pull/907)

- Fix documentation on v.21.2.0

### 34.4.2 [#905](https://github.com/openfisca/openfisca-core/pull/905)

- Fix minor errors that result in operations being uselessly repeated over and over.

### 34.4.1 [#904](https://github.com/openfisca/openfisca-core/pull/904)

- Improve performance graph introduced in 34.4.0
  - Sort frames by calculation time
  - Increase graph precision
  - Make the HTML graph self-supported: it can now be open with a simple browser, without starting a local server

## 34.4.0 [#895](https://github.com/openfisca/openfisca-core/pull/895)

#### New features

- Introduce the time performance flame graph
  - Generates a flame graph in a web page to view the time taken by every calculation in a simulation
  - Introduces `--performance` option to `openfisca test` command to generate a YAML test graph

#### Usage notes

1. To generate the flame graph:
  * For a Python simulation:

    ```py
    tax_benefit_system = CountryTaxBenefitSystem()
    simulation = SimulationBuilder().build_default_simulation(tax_benefit_system)

    simulation.trace = True  # set the full tracer
    [... simulation.calculate(...) ...]
    simulation.tracer.performance_log.generate_graph(".")  # generate graph in chosen directory
    ```

  * For a YAML test, execute the test with the `--performance` option.

      For example, to run the `irpp.yaml` test in `openfisca-france/` run:
      ```sh
      openfisca test tests/formulas/irpp.yaml --performance -c openfisca_france
      ```
      This generates an `index.html` file in the current directory.

2. From the current directory, run a Python web server (here on port `5000`):

    `python -m http.server 5000`

3. See the flame graph result in your browser at `http://localhost:5000`.
  This interprets the generated `index.html`.

When your yaml file contains multiple tests, only the last one is displayed in the flame chart.
You can use [openfisca test --name_filter option](https://openfisca.org/doc/openfisca-python-api/openfisca-run-test.html) to choose a specific test case.

### 34.3.3 [#902](https://github.com/openfisca/openfisca-core/pull/902)

#### Technical change

- Update dependency: numexpr

### 34.3.2 [#901](https://github.com/openfisca/openfisca-core/pull/901)

#### Technical change

- Update dependency: numpy

### 34.3.1 [#900](https://github.com/openfisca/openfisca-core/pull/900)

#### Bug fix

- Fix serialisation error introduced in [34.2.9](https://github.com/openfisca/openfisca-core/tree/34.2.9) in route `/trace` (Web API)
  - This was causing an Internal Server Error
  - Notably, `numpy` arrays were not being parsed correctly as not JSON serialisable

### 34.3.0 [#894](https://github.com/openfisca/openfisca-core/pull/894)

_Note: this version has been unpublished due to an issue introduced by 34.2.9 in the Web API. Please use 34.3.1 or a more recent version._

- Update pytest version's upper bound to 6.0.0

### 34.2.9 [#884](https://github.com/openfisca/openfisca-core/pull/884)

_Note: this version has been unpublished due to an issue introduced by 34.2.9 in the Web API. Please use 34.3.1 or a more recent version._

- Refactor simulation tracer implementation
  - These changes should be transparent for users
  - They should enable more precise performance measures, to come in a later version.

### 34.2.8 [#892](https://github.com/openfisca/openfisca-core/pull/892)

#### Documentation

- Update links to the doc in the API

### 34.2.7 [#886](https://github.com/openfisca/openfisca-core/pull/885)

#### Minor change

- Enforce type checking in tests and Continuous Integration

### 34.2.6 [#886](https://github.com/openfisca/openfisca-core/pull/886)

#### Minor change

- Remove remaining of extra-parameters handling, since that feature was removed in 28.0

### 34.2.5 [#888](https://github.com/openfisca/openfisca-core/pull/888)

#### Technical changes

- Define a trim option for average rate function.
- Convert a dict_values to a list (left-over by the python 3 migration)
- Use a less stric version dependency for psutils. Problem arising with psutils are mainly due to freeze at install. Use `pip` option `--no-cache-dir` if you face troubles at install.

### 34.2.4 [#870](https://github.com/openfisca/openfisca-core/pull/870)

#### Bug fix

- Avoid column-wrapping array values in debug strings

### 34.2.3 [#883](https://github.com/openfisca/openfisca-core/pull/883)

#### Technical changes

- Update dependency: psutil

### 34.2.2 [#873](https://github.com/openfisca/openfisca-core/pull/873)

#### Bug fixes

- Fix incomplete initialization of group entities provided by default when not supplied in YAML tests

### 34.2.1 [#882](https://github.com/openfisca/openfisca-core/pull/882)

#### Technical changes

- Update dependencies: NumPy, Flask, dpath, numexpr

## 34.2.0 [#872](https://github.com/openfisca/openfisca-core/pull/872)

#### New features

- Allow formulas to return scalar values; broadcast these values to population-sized arrays

## 34.1.0 [#876](https://github.com/openfisca/openfisca-core/pull/876)

#### New features

- Support role indices in SimulationBuilder.join_with_persons
  - This broadens the range of input data we can handle, at some risk of misattributing roles

### 34.0.1 [#868](https://github.com/openfisca/openfisca-core/pull/868)

#### Bug fix

- Allow both `*.yaml` and `*.yml` extensions for YAML tests

# 34.0.0 [#867](https://github.com/openfisca/openfisca-core/pull/867)

#### Technical changes

- Use pytest instead of nose in `openfica test`

### Breaking changes

- Remove `generate_tests` function from `openfisca_core.tools.test_runner`:
  - While this function was public and documented, its purpose was primarily internal and is unlikely to have been directly used by users.

### 33.0.1 [#865](https://github.com/openfisca/openfisca-core/pull/865)

- Improve error message when too many persons are given a role with a `max` attribute
    - This error typically happens when 3 parents are declared in a family, while the entity declaration specifies there can be at most 2.

# 33.0.0 [#866](https://github.com/openfisca/openfisca-core/pull/866)

### Breaking changes

- Duplicate keys in YAML parameter files now raise an error
    - Before, only one of the two values declared was taking into account, while the other was silently ignored

### 32.1.1 [#864](https://github.com/openfisca/openfisca-core/pull/864)

- Fix host in the `/spec` route of the Web API
  - The host should not include the HTTP scheme (http or https)

## 32.1.0 [#863](https://github.com/openfisca/openfisca-core/pull/863)

- Display symbolic values of Enums in /trace and print_computation_log

# 32.0.0 [#857](https://github.com/openfisca/openfisca-core/pull/857)

### Breaking changes

- Split the "Entity" class hierarchy (Entity, PersonEntity, GroupEntity) into two parallel hierarchies, representing respectively the abstract, model-level information (classes named Entity etc.) and the population-level information (classes named Population and GroupPopulation)
  - As a result, the first parameter passed to a formula is now a Population instance
  - Much more detail (and class diagrams) in the PR description
- Remove support from the syntax `some_entity.SOME_ROLE` to access roles (where `some_entity` is the entity passed to a formula).

#### Migration details

- Use the standard SomeEntity.SOME_ROLE instead. (Where SomeEntity is the capitalized entity or instance, Household.PARENT.)
- Code that relied excessively on internal implementation details of Entity may break, and should be updated to access methods of Entity/Population instead.

# 31.0.1 [#840](https://github.com/openfisca/openfisca-core/pull/840)

- Improve usability of Enum values:
- Details:
  - Allow the use of Enum values in comparisons: instead of using `<Enum class>.possible_values` you can simply `import` the Enum class
  - Accept Enum values via set_input (same result as the previous point)

# 31.0.0 [#813](https://github.com/openfisca/openfisca-core/pull/813)

#### Breaking changes

- Require clients to make explicit when input variables cover a range of dates, rather than allowing inputs to be derived from past or future values; also removes the `missing_value` base function

#### Migration notes

You might need to change your code if any of the following applies:
- you are a model author, and there are variables in your model that use a `base_function` attribute
- your model **or application** uses any non-numeric variables (boolean, date, string or Enum) used in, for which the period on which you define **inputs** does not match the period for which you are requesting **outputs**

Detailed instructions are provided in the [PR description](https://github.com/openfisca/openfisca-core/pull/813).

### 30.0.3 [#859](https://github.com/openfisca/openfisca-core/pull/859)

- Raise an error instead of silently ignoring the input when a user tries to set an input for a variable for several months (or several years), but the variable has no `set_input` declared.

### 30.0.2 [#860](https://github.com/openfisca/openfisca-core/pull/860)

- Apply `flake8-bugbear` recommendations and enforce same in continuous integration.

### 30.0.1 [#855](https://github.com/openfisca/openfisca-core/pull/855)

- Remove Python 2 compatibility code.

# 30.0.0 [#817](https://github.com/openfisca/openfisca-core/pull/817)

#### Breaking changes

- Improve cycle and spiral detection, giving consistent results more systematically

#### Migration notes

- Remove all optional parameters `max_nb_cycles`
- Avoid relying on cached values of a computation

For additional details, see the PR's [description](https://github.com/openfisca/openfisca-core/pull/817).

### 29.0.2 [#858](https://github.com/openfisca/openfisca-core/pull/858)

#### Bug fix

- Fix error on simulation debug attribute at simulation clone
- Details:
  - Fixes `AttributeError: 'Simulation' object has no attribute 'debug'` introduced by Core v.`29.0.0`.

### 29.0.1 [#851](https://github.com/openfisca/openfisca-core/pull/851)

- Remove print statements from `simulations.py`, add linting options to detect stray print statements

# 29.0.0 [#843](https://github.com/openfisca/openfisca-core/pull/843)

#### Breaking changes

- Remove argument `simulation_json` of `Simulation` constructor, which was deprecated as of Core 25
- Remove keyword arguments from Simulation constructor, which should be called only from SimulationBuilder; introduce a property for `trace`
- Remove `period` attribute of Simulation

#### Migration notes

- As of Core 25, the preferred way of constructing new Simulation instances is via SimulationBuilder, any remaining uses of scenarios should be migrated to that API first.
- Any period attribute of the Simulation was coming from the simulation data (test case or JSON structure), use that instead of the attribute in the Simulation instance.
- Any keyword arguments of Simulation that you were using (or passing to Simulation-constructing methods) can now be accessed directly or as properties, `trace` being the most widely used. Example below:

**Before**

```Python
simulation = SimulationBuilder().build_from_entities(tax_benefit_system, input_data, trace = True)
```

**After**

```Python
simulation = SimulationBuilder().build_from_entities(tax_benefit_system, input_data)
simulation.trace = True
```

### 28.0.1 [#845](https://github.com/openfisca/openfisca-core/pull/845)

- Consistently use the safe approach to YAML loading, fixing [this deprecation warning](https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation) introduced in PyYAML 5.1

# 28.0.0 [#847](https://github.com/openfisca/openfisca-core/pull/847)

#### Breaking changes

Remove extra_params altogether from Core. This puts all formulas on an equal footing and simplifies
simulation and data storage code.

#### Migration notes

For almost all users, no migration is needed.

You may be impacted only if you were computing (for instance in a notebook) one of the two variables from France that used this non-standard extension to the `calculate(variable, period)` API: `rsa_fictif` or `ppa_fictive`. In that case you had to supply the additional parameter `mois_demande`. Use `rsa` or `ppa` directly, and go back to the standard API.

### 27.0.2 [#844](https://github.com/openfisca/openfisca-core/pull/844)

> Note: Versions `27.0.0` and `27.0.1` have been unpublished as the former accidentally introduced a bug affecting test inputs. Please use version `27.0.2` or more recent.

- Fix a bug introduced in 27.0.0, affecting YAML tests; because of an incorrect date comparison, input variables would be ignored if they had an end date.

### 27.0.1 [#839](https://github.com/openfisca/openfisca-core/pull/839)

#### Technical changes

- Provide three levels of information when running tests depending on context:
  - when running `pytest`, all failures are reported, coverage is omitted
  - when running `make test`, all failures are reported, with coverage also reported
  - in continuous integration, exit on first failure, but report coverage always

# 27.0.0 [#826](https://github.com/openfisca/openfisca-core/pull/826)

#### Breaking changes

- No longer honor calls to `set_input` for variables which have an end date and for periods after that date.

#### Migration guide

This change is not expected to actually break much reusing code (if any), as it is unlikely that one would deliberately specify an end date for a variable and use it in computations for periods past that date. However, nothing has previously ruled out relying on that behaviour and it may have been introduced by accident. In particular, it can happen that a variable with a formula and an end date is also, in some applications, used as an input.

## 26.2.0 [#833](https://github.com/openfisca/openfisca-core/pull/833)

- Introduce a way to build a simulation for tabular inputs

#### New features

- Allow to create a simulation step by step:
  1. Create entities with `SimulationBuilder.create_entities(...)`
  2. Declare your population
      with `SimulationBuilder.declare_person_entity(...)` and `SimulationBuilder.declare_entity(...)`
  3. Link between persons in population definition with `SimulationBuilder.join_with_persons(...)`
  4. Build a simulation with `SimulationBuilder.build(...)`
  5. Set variable values with the already existing `Simulation.set_input(...)` method

## 26.1.0 [#835](https://github.com/openfisca/openfisca-core/pull/835)

- No longer raise an error when a group entity is not specified in a test case, or partially specified.
  - Instead, each person is by default allocated to a group of which they are the sole member, with the default role in that group.

### 26.0.6 [#836](https://github.com/openfisca/openfisca-core/pull/836)

- Convert tests that were incompatible with Pytest 4.0+ and reported "xfail" when run with that version

### 26.0.5 [#829](https://github.com/openfisca/openfisca-core/pull/829)

- Update autopep8 and flake8, which in particular now enforce rules W504 and W605
  - W504 goes against house style, so we add it to ignored rules
  - W605 may seem like an [overreach](https://github.com/PyCQA/pycodestyle/issues/755) but does make sense (additional details in PR description), so we upgrade a few regexes to raw strings

### 26.0.4 [#825](https://github.com/openfisca/openfisca-core/pull/825)

- Fixes regression introduced by Core v25 when running YAML tests with reforms or extensions

### 26.0.3 [828](https://github.com/openfisca/openfisca-core/pull/828)

- Remove `__future__` statements
  - As Python 2 support has been dropped, they are not needed anymore.

### 26.0.2 [830](https://github.com/openfisca/openfisca-core/pull/830)

- Collect and publish measurements of which lines of codes are exercised (or not) by our tests

### 26.0.1 [831](https://github.com/openfisca/openfisca-core/pull/831)

- Greet visitors to our Github repo with badges providing contact and code information

# 26.0.0 [#790](https://github.com/openfisca/openfisca-core/pull/790)

#### What this PR brings

An exciting but under-documented feature, "axes", now has much better test coverage and thus long-term maintainability (the documentation is still lacking, but see https://github.com/openfisca/tutorial for demos)

#### Breaking changes

This PR deprecates the `new_scenario` approach to constructing Simulation objects. This will impact you if:
- your notebooks or scripts or other Python code rely on the France model and use the old form of creating a Simulation object (see below)
- **or** your country package defines a Scenario class and injects it [the way France does](https://github.com/openfisca/openfisca-france/blob/11b18985ce4decc31b5666114b2525dddf42652b/openfisca_france/france_taxbenefitsystem.py#L29)

**To migrate to this version**, if you are in the first case, the minimum required change is this:

*The old way:*
```
simulation = tax_benefit_system.new_scenario().init_single_entity(...some data...).new_simulation()
```
*The new way:*
```
# At the top of your file
from openfisca_france.scenarios import init_single_entity
# Below
simulation = init_single_entity(tax_benefit_system.new_scenario(), ...some data...).new_simulation()
```

If you are in the latter case, you must also transform your `init_single_entity` from a Scenario method to a regular function at global scope, and change your tests and reuses as described above.

### 25.3.4 [827](https://github.com/openfisca/openfisca-core/pull/827)

- Optimize `set_input_dispatch_by_period` so that it doesn't create duplicate vectors in memory

### 25.3.3 [821](https://github.com/openfisca/openfisca-core/pull/821)

- Bring up the debugger on integration test failures with `openfisca test --pdb` optional argument

### 25.3.2 [824](https://github.com/openfisca/openfisca-core/pull/824)

- Rename LICENSE.AGPL.txt to LICENSE to let github recognize it

### 25.3.1 [#820](https://github.com/openfisca/openfisca-core/pull/820)

- Outputs a more helpful message when a variable checked in a test doesn't exist
- Introduces unit tests for the test runner

## 25.3.0 [#811](https://github.com/openfisca/openfisca-core/pull/811)

#### Technical changes

- Allow France to model "Chèque Energie" in a cleaner way:
  - Introduce SingleAmountTaxScale (SATS), a simpler form of MarginalAmountTaxScale (MATS)
    - whereas MATS sums the values in brackets, up to the amount subject to the scale, SATS only "looks up" the appropriate value for the amount subject to the scale, and is thus the simpler mechanism
    - use `numpy.digitize`, allowing callers to specify right or left intervals
    - introduce a `type` tag in `brackets` object, thus far with only `single_amount` allowed
  - Rename AmountTaxScale to MarginalAmountTaxScale and make it inherit from SATS

This is non-breaking, as there are no direct clients of these classes outside of Core.

### 25.2.9 [#814](https://github.com/openfisca/openfisca-core/pull/814)

- When a YAML test fails, display the correct period for wrong output variable

### 25.2.8 [#815](https://github.com/openfisca/openfisca-core/pull/815)

- Quell a warning in the build of openfisca-doc by moving a docstring to the right place

### 25.2.7 [#803](https://github.com/openfisca/openfisca-core/pull/803)

- Allow country package users to run `openfisca test` without installing the `web_api` dependency
- Alias `openfisca-run-test` to `openfisca test`

### 25.2.6 [#797](https://github.com/openfisca/openfisca-core/pull/797)

- Improve `print_computation_log` and make it a tested, thus supported call

### 25.2.5 [#802](https://github.com/openfisca/openfisca-core/pull/802)

- Load extensions more reliably, by removing dead code in load_extension

### 25.2.4 [#806](https://github.com/openfisca/openfisca-core/pull/806)

- Supply a missing default parameter in `Simulation.delete_arrays` method.

### 25.2.3 [#800](https://github.com/openfisca/openfisca-core/pull/800)

- Fix an exception on yaml import in test runner

### 25.2.2 [#798](https://github.com/openfisca/openfisca-core/pull/798)

- Fix a regression in the YAML test runner. If you have changed any YAML tests since 25.0.0, please rerun them.

### 25.2.1 [#796](https://github.com/openfisca/openfisca-core/pull/796)

- Update documentation URL in the API welcome message

### 25.2.0 [#766](https://github.com/openfisca/openfisca-core/pull/766)

- Support DAY periods

### 25.1.1 [#794](https://github.com/openfisca/openfisca-core/pull/794)

- Explicit test runner dependencies in Python 2.7
  - Using an older version of `ruamel` caused a `'CommentedSeq' object has no attribute 'get'` error.

## 25.1.0 [#787](https://github.com/openfisca/openfisca-core/pull/787)

- Don't sort JSON keys in the Web API
  - By default, `flask` sorts JSON _object_ keys alphabetically
  - This is useful for reusing http caches for example, at the cost of some performance overhead
  - But the [JSON specification](https://www.json.org/) doesn’t require to keep an order, as _objects_ are defined as "an unordered set of name/value pairs"

# 25.0.0 [#781](https://github.com/openfisca/openfisca-core/pull/781)

#### Breaking changes

  - Change the syntax of OpenFisca YAML tests

  For instance, a test that was using the `input_variables` keyword like:

  ```yaml
  - name: Basic income
    period: 2016-12
    input_variables:
      salary: 1200
    output_variables:
      basic_income: 600
  ```

  becomes:

  ```yaml
  - name: Basic income
    period: 2016-12
    input:
      salary: 1200
    output:
      basic_income: 600
  ```

  A test that was fully specifying its entities like:

  ```yaml
  name: Housing tax
  period: 2017-01
  households:
    - parents: [ Alicia ]
      children: [ Michael ]
  persons:
    - id: Alicia
        birth: 1961-01-15
    - id: Michael
        birth: 2002-01-15
  output_variables:
    housing_tax:
      2017: 1000
  ```

  becomes:

  ```yaml
  name: Housing tax
  period: 2017-01
  input:
    household:
      parents: [ Alicia ]
      children: [ Michael ]
    persons:
      Alicia:
        birth: 1961-01-15
      Michael:
        birth: 2002-01-15
  output:
    housing_tax:
      2017: 1000
  ```

  A **migration script** is available to automatically convert tests:

  ```sh
  python openfisca_core/scripts/migrations/v24_to_25.py /path/to/tests/
  ```

  > Note for country packages using Scenarios (e.g. France, Tunisia):
  > Tests are not using scenarios anymore. Therefore, tests cannot partially specify entities anymore. Tests using entities inference may need manual adaptation in addition to the script.

  - The `Entity` constructor (usually not directly called by users) does not accept an `entities_json` parameter anymore.


#### Deprecation

  - Deprecate `openfisca-run-test`
    - `openfisca test` should be used instead.

  - Deprecate the use of the `simulation_json` parameter in the `Simulation` constructor.
    - `SimulationBuilder(tax_benefit_system).build_from_entities(simulation_json)` should be used instead


#### New features

  - In YAML tests, allow to define expected output for a specific entity

  For instance:

  ```yaml
name: Housing tax
period: 2017-01
input:
  ...
output:
  persons:
    Alicia:
      salary: 3000
  ```

  - In YAML tests, allow to specify an extension to use to run the test:
    - See [example](https://github.com/openfisca/openfisca-core/blob/25.0.0/tests/core/yaml_tests/test_with_extension.yaml)

  - In YAML tests, allow the use of YAML anchors:
    - See [example](https://github.com/openfisca/openfisca-core/blob/25.0.0/tests/core/yaml_tests/test_with_anchors.yaml)

  - Introduce [`EnumArray.decode_to_str`](https://openfisca.org/doc/openfisca-python-api/enum_array.html#openfisca_core.indexed_enums.EnumArray.decode_to_str)


#### Architecture changes

  - Move the complex initialisation logics (for JSON-like inputs) to `SimulationBuilder`, away from the `Simulation` and `Entity` classes

## 24.11.0 [#791](https://github.com/openfisca/openfisca-core/pull/791)

- In Python, simplify getting known periods for variable in a simulation:

Before:

```py
simulation = ...
holder = simulation.persons.get_holder('salary')
holder.get_known_periods()
```

After:

```py
simulation = ...
simulation.get_known_periods('salary')
```

## 24.10.0 [#784](https://github.com/openfisca/openfisca-core/pull/784)

- In Python, simplify simulation array deletion:

Before:

```py
simulation = ...
holder = simulation.persons.get_holder('salary')
holder.delete_arrays('2018-08')
```

After:

```py
simulation = ...
simulation.delete_arrays('salary', '2018-08')
```

### 24.9.9 [#786](https://github.com/openfisca/openfisca-core/pull/786)

- Set a 120s default timeout in `openfisca serve`
  - Otherwise, they regularly restart with an anxiety-provoking "[CRITICAL] WORKER TIMEOUT (pid:2137)" message in log

### 24.9.8 [#780](https://github.com/openfisca/openfisca-core/pull/780)

- Allow non-integral inputs to int variables

### 24.9.7 [#769](https://github.com/openfisca/openfisca-core/pull/769)

- Ensure `path.to.parameter` syntax works consistently across country and extension

### 24.9.6 [#771](https://github.com/openfisca/openfisca-core/pull/771)

- Improve serve command by documenting the bind option
- Avoid crashing when no arguments are supplied

### 24.9.5 [#774](https://github.com/openfisca/openfisca-core/pull/774)

- Clarify the error message when assigning a value larger than MaxInt32 to an 'int' variable

### 24.9.4 [#777](https://github.com/openfisca/openfisca-core/pull/777)

- Allow OpenFisca-Core users to define their own level of log

### 24.9.3 [#778](https://github.com/openfisca/openfisca-core/pull/778)

- Remove the reference doc source, as it's been moved to https://github.com/openfisca/openfisca-doc.
- Rebuild the doc when the Core codebase changes

### 24.9.2 [#776](https://github.com/openfisca/openfisca-core/pull/776)

- Allow `ParameterNode` children to have a numeric keys
  - Before, an incorrect id would be set for these children, resulting to inconsistencies in the Web API.

### 24.9.1 [#770](https://github.com/openfisca/openfisca-core/pull/770)

- Fix a bug that prevented amount scale parameters from being accessed in a formula

## 24.9.0 [#767](https://github.com/openfisca/openfisca-core/pull/767)

- Introduce `ParameterNode.get_descendants`
  - This method returns a generator containing all the parameters and nodes recursively contained in the `ParameterNode`

### 24.8.2 [#773](https://github.com/openfisca/openfisca-core/pull/773)

- Make sure to cap all dependency versions, in order to avoid unwanted functional and integration breaks caused by external code updates
  - For example [#772](https://github.com/openfisca/openfisca-core/pull/772)

### 24.8.1 [#772](https://github.com/openfisca/openfisca-core/pull/772)

- Limits the range of PyTest versions to < 4.0 to avoid CI crashes caused by 4.0.

## 24.8.0 [#765](https://github.com/openfisca/openfisca-core/pull/765)

- Adds called parameters to Web API `/trace` endpoint
  - For a calculated variable, add `parameters` item next to `dependencies` in `/trace` response
  - For example:
  ```JSON
    {
      "income_tax<2017-01>": {
        "dependencies": [
          "salary<2017-01>"
        ],
        "parameters": {
          "taxes.income_tax_rate<2017-01-01>": 0.15
        },
        "value": [150]
      }
    }
  ```
  - Scale parameters are also traced:
  ```json
    "parameters": {
      "taxes.social_security_contribution<2017-01-01>": {
          "0.0": 0.02,
          "12400.0": 0.12,
          "6000.0": 0.06
      }
    },
  ```

### 24.7.0 [#756](https://github.com/openfisca/openfisca-core/pull/756)

- Exposes `amount` scales through the Web API
  - Allows for [AmountTaxScale](https://github.com/openfisca/openfisca-core/blob/2b76b2ae5f684832411694c7c763b2d84c521c3c/openfisca_core/taxscales.py#L119) parameters to be consumed through the Web API
  - See for an example this [parameter in openfisca-tunisia](https://github.com/openfisca/openfisca-tunisia/blob/10a15168e0aab5000f6850ad2f7779eba5da0fe0/openfisca_tunisia/parameters/impot_revenu/contribution_budget_etat.yaml)

### 24.6.8 [#753](https://github.com/openfisca/openfisca-core/pull/753)

- Always allow `documentation` property for `ParameterNode`
  - Due to a bug, this field  was accepted in an `index.yaml` file, but not in a `ParameterNode` located in a single YAML file

### 24.6.7 [#760](https://github.com/openfisca/openfisca-core/pull/760)

- Tests the computation of the average tax rate of a targeted net income, according to the varying gross income.

### 24.6.6 [#758](https://github.com/openfisca/openfisca-core/pull/758)

- Updates the requirements on [numpy](http://www.numpy.org) to permit version 1.16

### 24.6.5 [#751](https://github.com/openfisca/openfisca-core/pull/751)

- Fix unproper `entity.count` restoration of a dumped simulation
- Use more previsible value for average rate even when a division by zero is present

### 24.6.4 [#752](https://github.com/openfisca/openfisca-core/pull/752)

- Improve the warning message incentivizing users to install `libyaml`
  - `pyyaml` needs to be fully reinstalled to use `libyaml`

### 24.6.3 [#746](https://github.com/openfisca/openfisca-core/pull/746)

- Use `pytest` to run tests, as `nose` and `nose2` are not in active development anymore
- Declare `nose` as a dependency so dependee libraries like `openfisca-france`can use `openfisca-run-test` without having to add `nose` as a dependency

_Note: `openfisca-run-test` still depends on `nose`._


### 24.6.2 [#735](https://github.com/openfisca/openfisca-core/pull/735)

- Apply W504 enforcement (Knuth's style)
- Removes version cap on linting libraries

## 24.6.1 [#745](https://github.com/openfisca/openfisca-core/pull/745)

- Fix `host` property in the OpenAPI `/spec`
  - It should not contain the scheme (e.g. `http`)
- Infer scheme from request
  - Before, we would assume `https`, which is not always accurate

## 24.6.0 [#744](https://github.com/openfisca/openfisca-core/pull/744)

- Allow TaxBenefitSystem to define the examples to use in the `/spec` route.
  - See [docs](https://openfisca.org/doc/openfisca-web-api/config-openapi.html).

### 24.5.6 [#743](https://github.com/openfisca/openfisca-core/pull/743)

- When there is an empty `index.yaml` in the parameters, ignore it instead of raising an error.

### 24.5.5 [#742](https://github.com/openfisca/openfisca-core/pull/742)

- Fix the internal server error that appeared for the  `/trace` and (less frequently) `/calculate` route of the Web API
  - This error appeared when a simulation output was a variable of type string


> Note: Versions `24.5.3` and `24.5.4` have been unpublished as they accidentally introduced a breaking change. Please use version `24.5.5` or more recent.


### 24.5.2 [#734](https://github.com/openfisca/openfisca-core/pull/734)

- Ignore W503 to enforce Knuth's style (W504)
- Fix failing entities test
  - Household description was outdated

### 24.5.1 [#732](https://github.com/openfisca/openfisca-core/pull/732)

- Further adopt simplified simulation initialisation
  - See [#729](https://github.com/openfisca/openfisca-core/pull/729)

## 24.5.0 [#729](https://github.com/openfisca/openfisca-core/pull/729)

- In Python, simplify simulation initialisation:

Before:

```py
simulation = ...
holder = simulation.persons.get_holder('salary')
holder.set_input('2018-08', [4000])
```

After:

```py
simulation = ...
simulation.set_input('salary', '2018-08', [4000])
```

## 24.4.0 [#717](https://github.com/openfisca/openfisca-core/pull/717)

- In Python, allow multiline documentation on parameters and variables
  - Introduce `documentation` attribute on `ParameterNode`, `Parameter` and `Variable` classes

- In the Web API, expose this documentation as a `documentation` property for parameters, variables and variables' formulas
    - on `/parameter` nodes as `/parameter/benefits`
      > = python `ParameterNode.documentation`
      > = YAML parameter node (`index.yaml`) `documentation` string attribute
    - on `/parameter` leafs as `/parameter/benefits/housing_allowance`
      > = python `Parameter.documentation`
      > = YAML parameter `documentation` string attribute
    - on `/variable` as `/variable/housing_allowance`
      > = python `Variable.documentation`
    - on every `/variable` leaf formula
      > = python `Variable` formula **docstring**

### 24.3.2 [#727](https://github.com/openfisca/openfisca-core/pull/727)

- Add a style formatter that follows community code conventions
- Auto-fix code formatting

### 24.3.1 [#723](https://github.com/openfisca/openfisca-core/pull/723)

- Fix small issues in the `/spec` route of the Web API
  - Use proper JSON Schema type to describe input types
  - Fix property name in the description of `/parameters` and `/variables`

### 24.3.0 [#714](https://github.com/openfisca/openfisca-core/pull/714)

- Introduce the `/entities` endpoint for the Web API.
  - Expose information about the country package's entities, and their roles.
```json
{
            "description": "Household",
            "documentation": "Household is an example of a group entity. A group entity contains one or more individual·s.[...]",
            "plural": "households",
            "roles": {
                "parent": {
                    "description": "The one or two adults in charge of the household.",
                    "max": 2,
                    "plural": "parents"
                    },
                "child": {
                    "description": "Other individuals living in the household.",
                    "plural": "children"
                    }
                }
            }
```

## 24.2.0 [#712](https://github.com/openfisca/openfisca-core/pull/712)

- Allow to dump and restore a simulation in a directory

Dump:

```py
from openfisca_core.tools.simulation_dumper import dump_simulation
dump_simulation(simulation, '/path/to/directory')
```

Restore:

```py
from openfisca_core.tools.simulation_dumper import restore_simulation
simulation = restore_simulation('/path/to/directory', tax_benefit_system)
```

### 24.1.0 [#713](https://github.com/openfisca/openfisca-core/pull/713)

- Enhance navigation within the Openfisca Web API.
- Provides a direct link to individual parameters and variables from the `/parameters` and `/variables` routes.

The former `/parameters` route of the Web API:

```json
"benefits.basic_income": {
        "description": "Amount of the basic income",
        },
"benefits.housing_allowance": {
        "description":"Housing allowance amount (as a fraction of the rent)",
        },
    ...
```

becomes:

```json
"benefits.basic_income": {
        "description": "Amount of the basic income",
        "href":"http://localhost:5000/parameter/benefits.basic_income"
        },
"benefits.housing_allowance": {
        "description":"Housing allowance amount (as a fraction of the rent)",
        "href":"http://localhost:5000/parameter/benefits.housing_allowance"
        },
    ...
```

### 24.0.1 [#711](https://github.com/openfisca/openfisca-core/pull/711)

- Fix spelling in warning about libyaml

# 24.0.0 [#703](https://github.com/openfisca/openfisca-core/pull/703)

#### Breaking changes

##### Only install the Web API dependencies as an opt-in:

- `pip install OpenFisca-Core` will _not_ install the Web API anymore.
- `pip install OpenFisca-Core[web-api]` will.

Country package maintainers who still want to provide the Web API by default with their package (**recommended**) should update their `setup.py`:
  - In the `install_requires` section, replace `'OpenFisca-Core >= 23.3, < 24.0'` by `'OpenFisca-Core[api] >= 24.0, < 25.0'`
  - See [example](https://github.com/openfisca/country-template/commit/b75eea97d8d22091a3f13a580118ce45b16f4294)

##### Change default Web API port to 5000:

- `openfisca serve` will now serve by default on the `5000` port instead of `6000` (blocked by Chrome).

##### Rename OpenFisca Web Api package to `openfisca_web_api`:

- Transparent for users of the `openfisca serve` command.
- Users who used to manually import `openfisca_web_api_preview` must know import `openfisca_web_api`.

##### Rename development dependencies from `test` to `dev`:

- Developpers should now run `pip install --editable .[dev]` instead of `pip install --editable .[test]` to install them.

#### New features

- In the `/spec` route:
  - Indicate the served country package version as API version (instead of `0.1.0`).
  - Infer the host URL from the requests, instead of relying on the undocumented `SERVER_NAME` environnement variable.
    - The use of the `SERVER_NAME` environnement variable is therefore deprecated and without effect.

### 23.5.2 [#710](https://github.com/openfisca/openfisca-core/pull/710)

- Revert the undesired side effects of `23.4.0` on the `parameters/` overview route of the Web API
  - This route now behaves the exact same way than before `23.4.0`
  - The keys of the `/parameters` JSON object are back to using the `.` notation
  - Parameter nodes are for now not exposed in the `parameters/` overview (but each of them is exposed in `/parameter/path/to/node`)

### 23.5.1 [#708](https://github.com/openfisca/openfisca-core/pull/708)
_Note: this version has been unpublished due to an issue introduced by 23.4.0 in the Web API. Please use 23.5.2 or a more recent version._

- Remove the irrelevant decimals that were added at the end of `float` results in the Web API and the test runner.
  - These decimals were added while converting a NumPy `float32` to a regular 64-bits Python `float`.

For instance, the former Web API response extract:

```json
  "tax_incentive": {
        "2017-01": 333.3333435058594
      }
```

becomes:

```json
"tax_incentive": {
        "2017-01": 333.33334
      }
```

## 23.5.0 [#705](https://github.com/openfisca/openfisca-core/pull/705)
_Note: this version has been unpublished due to an issue introduced by 23.4.0 in the Web API. Please use 23.5.2 or a more recent version._

* On the Web API, expose a welcome message (with a 300 code) on `/` instead of a 404 error.

For instance, `curl -i localhost:5000` gives:

```
HTTP/1.1 300 MULTIPLE CHOICES
(...)

{
  "welcome": "This is the root of an OpenFisca Web API. To learn how to use it, check the general documentation (https://openfisca.org/doc/api) and the OpenAPI specification of this instance (http://localhost:5000/spec)."
}
```

* This message can be customized:

If the Web API is started with `openfisca serve -p 3000 --welcome-message "Welcome to the OpenFisca-France Web API. To learn how to use it, check our interactive swagger documentation: https://fr.openfisca.org/legislation/swagger."`

Then `curl -i localhost:5000` gives:

```
HTTP/1.1 300 MULTIPLE CHOICES
(...)

{
  "welcome": "Welcome to the OpenFisca-France Web API. To learn how to use it, check our interactive swagger documenation: https://fr.openfisca.org/legislation/swagger"
}
```

(Like other configuration variables, this custom message can also be defined in a configuration file. Check the [openfisca serve documentation](https://openfisca.readthedocs.io/en/latest/openfisca_serve.html))


### 23.4.1 [#700](https://github.com/openfisca/openfisca-core/pull/700)
_Note: this version has been unpublished due to an issue introduced by 23.4.0 in the Web API. Please use 23.5.2 or a more recent version._

* Fix API source IP detection through proxies.

## 23.4.0 [#694](https://github.com/openfisca/openfisca-core/pull/694)
_Note: this version has been unpublished as it introduced an issue in the Web API. Please use 23.5.2 or a more recent version._

* Use `/` rather than `.` in the path to access a parameter:
  - For instance `/parameter/benefits.basic_income` becomes `/parameter/benefits/basic_income`
  - Using `.` is for now still supported, but is considered deprecated and will be turned to a 301 redirection in the next major version.

* Expose parameters `metadata` and `source` in the Web API and:

For instance, `/parameter/benefits/basic_income` contains:

```JSON
{
  "description": "Amount of the basic income",
  "id": "benefits.basic_income",
  "metadata": {
    "reference": "https://law.gov.example/basic-income/amount",
    "unit": "currency-EUR"
  },
  "source": "https://github.com/openfisca/country-template/blob/3.2.2/openfisca_country_template/parameters/benefits/basic_income.yaml",
  "values": {
    "2015-12-01": 600.0
  }
}
```

* Expose parameters nodes in the Web API
  - For instance, `/parameter/benefits` now exists and contains:

```JSON
{
  "description": "Social benefits",
  "id": "benefits",
  "metadata": {},
  "source": "https://github.com/openfisca/country-template/blob/3.2.2/openfisca_country_template/parameters/benefits",
  "subparams": {
    "basic_income": {
      "description": "Amount of the basic income"
    },
    "housing_allowance": {
      "description": "Housing allowance amount (as a fraction of the rent)"
    }
  }
}
```

Note that this route doesn't _recursively_ explore the node, and only exposes its direct children name and description.


### 23.3.2 [#702](https://github.com/openfisca/openfisca-core/pull/702)

Minor Change without any impact for country package developers and users:
  - Make code more Python3-like by backporting unicode litterals.
  - With this backport, all strings are by default unicodes.
  - The `u` prefix for strings should *not* be used anymore.
  - Each new module must start by `from __future__ import unicode_literals` for the backport to be effective.

### 23.3.1 [#682](https://github.com/openfisca/openfisca-core/pull/682)

* Send reference of the country-package and its version to the tracker so it will appear in the tracking statistics.

## 23.3.0 [#681](https://github.com/openfisca/openfisca-core/pull/681)

* Change the way metadata are declared for Parameter.

Before:
```YAML
description: Age of retirement
reference: https://wikipedia.org/wiki/retirement
unit: year
values: (...)
```

After:
```YAML
description: Age of retirement
metadata:
  reference: https://wikipedia.org/wiki/retirement
  unit: year
values: (...)
```

_Setting `unit` and `reference` out of `metadata` is considered deprecated, but still works for backward compatibility._

* Allow legislation coders to define their own medatada

* Expose in the Python API
    - Parameters metadata:
      - e.g. `parameters.taxes.rate.metadata['unit']`
    - Parameter value metadata:
      - e.g. `parameters.taxes.rate.values_list[0].metadata['unit']`
    - Parameter node description and metadata:
      - e.g. `parameters.taxes.metadata['reference']`, `parameters.taxes.description`
      - Note: Parameter descriptions (e.g. `parameters.taxes.rate.description`) were already exposed

## 23.2.0 [#689](https://github.com/openfisca/openfisca-core/pull/689)

* Introduce `TaxBenefitSystem.replace_variable`
  - Unlike `update_variable`, this method does _not_ keep any of the replaced variable in the new one.
  - See [reference documentation](https://openfisca.org/doc/openfisca-python-api/tax-benefit-system.html#openfisca_core.taxbenefitsystems.TaxBenefitSystem.replace_variable).

### 23.1.7 [#686](https://github.com/openfisca/openfisca-core/pull/686)

* Fix installation on Windows with Python 3.7
  - Require `psutil` version `5.4.6`, as `5.4.2` is incompatible with that environment.

### 23.1.6 [#688](https://github.com/openfisca/openfisca-core/pull/688)

* In the error message sent to a user trying to set a variable without specifying for which period, add an example for a variable defined for `ETERNITY`.

### 23.1.5 [#687](https://github.com/openfisca/openfisca-core/pull/687)

* Allow to set uncached variables when using a `memory_config`
  - Previously, trying to set variables listed in `variables_to_drop` of the `memory_config` had no effect.
  - Now this variables are still not cached, but they can be set by the user.

### 23.1.4 [#679](https://github.com/openfisca/openfisca-core/pull/679)

* Use C binding to load and dump Yaml (`CLoader` and `CDumper`)
  - For countries with several Yaml tests, they can take some time to run
  - Using the C bindings provided by `libyaml` adds a little performance boost

### 23.1.3 [#680](https://github.com/openfisca/openfisca-core/pull/680)

Fix test that was failing due to migration to HTTPS

### 23.1.2 [#671](https://github.com/openfisca/openfisca-core/pull/671)

- Minor technical improvement
  - Publish both Python 2 and Python 3 version on Pypi in CircleCI

### 23.1.1 [#661](https://github.com/openfisca/openfisca-core/pull/661)

- Fixup Python 3 compatibility

### 23.1.0 [#660](https://github.com/openfisca/openfisca-core/pull/660)

Make package compatible with Python 3

### 23.0.2 [#645](https://github.com/openfisca/openfisca-core/pull/645)

Start adapting OpenFisca to Python 3
- Imports are now all absolute imports
- `unicode_type` and `basestring_type` are now used for compatible type checking.
- All calls for sorted() use the key parameter
- Iteration on dict now uses dict.items()

### 23.0.1 [656](https://github.com/openfisca/openfisca-core/pull/656)

* Re-accept `int` values for `instant` in `tax_benefit_system.get_parameter_at_instant(instant)`
  * `int` values were accidently rejected since v23

# 23.0.0 [643](https://github.com/openfisca/openfisca-core/pull/643)

This changeset aims at simplifying the OpenFisca Core architecture.

Changes should be transparent for legislation modeling and web API usage.

It can impact users using the Python API (see Breaking changes part)

General architecture principles:
  - `Simulation` is the class in charge of running the calculations
  - `Holder` is the class in charge of keeping input and previously calculated values

#### Breaking changes

- Remove two (already deprecated) possible values for the variable attribute `base_function`:
  - `permanent_default_value`
  - `requested_period_added_value`

In `Holder`:
  - Remove deprecated constructor `Holder(simulation, variable)`
    - Use `Holder(entity, variable)` instead
  - Remove attributes:
    - `formula` and `real_formula`
      - Use `variable.formulas` instead (see more further down)
    - `array`
      - Use `get_array(period)` instead
  - Remove methods:
    - `calculate` and `compute`
      - Use `simulation.calculate` instead
    - `calculate_output`
      - Use `simulation.calculate_output` instead
    - `compute_add`
      - Use `simulation.calculate_add` instead
    - `compute_divide`
      - Use `simulation.calculate_divide` instead
    - `get_from_cache`
      - Use `get_array` instead
    - `graph`
  - Methods `set_input` and `put_in_cache` don't return anything anymore.

In `Simulation`:
  - Reorder constructor arguments
    - `tax_benefit_system` is now the first (mandatory) argument, and `simulation_json` the second (optional) one.
  - Remove attributes:
    - `holder_by_name`
      - Use `simulation.get_holder(...)` or `entity.get_holder(...)` instead
  - Remove methods:
    - `compute`
      - Use `calculate` instead
    - `compute_add`
      - Use `calculate_add` instead
    - `compute_divide`
        - Use `calculate_divide` instead
    - `parameters_at`
      - Use `simulation.tax_benefit_sytem.get_parameters_at_instant` instead
    - `graph`
    - `to_input_variables_json`
  - Undeprecate, but slightly change the behaviour of the `get_holder(variable)` method:
    - Optional second argument `default` is not accepted anymore
    - If no holder has yet been created for the variable, no error is raised, and a new holder is created and returned.

#### New features

- Introduce `variable.formulas`, a sorted dict containing all the formulas of a variable:

```py
tax_benefit_system.get_variable('basic_income').formulas
>>> SortedDict({
    '2015-12-01': <function formula_2015_12 at 0x1079aa500>,
    '2016-12-01': <function formula_2016_12 at 0x1079aa488>
    })
```

Each value is a simple python function.

- Make `holder.set_input` more flexible
  - It now accepts a string as `period`
  - It now accepts a list as `array`

#### Technical changes

- Remove module `formulas` and class `Formula`
  - Variables's formulas are now simple functions.
- Remove class `DatedHolder`
  - All calculation methods now return a simple numpy array
- Variables don't necessary have a base function anymore
  - Without a base function, the default behavior is to return the default value if there is no formula.

## 22.1.0 [#648](https://github.com/openfisca/openfisca-core/pull/648)

* Allow two variable file to have the same name in a tax and benefit system
  - A [collision](https://github.com/openfisca/openfisca-core/issues/642) between module names made it impossible so far.

### 22.0.10 [#654](https://github.com/openfisca/openfisca-core/pull/654)

* Fix `dtype` attribute for `EnumArray`s (returned when calculating a variable of `value_type` `Enum`):
  - It was the type `numpy.int16` and not the dtype instance `numpy.dtype(numpy.int16)`
  - This caused issue when trying to export an `EnumArray` with `pandas`

### 22.0.9 [#650](https://github.com/openfisca/openfisca-core/pull/5O)

* Fix operators such as `household.first_parent`, `foyer_fiscal.declarant_principal` for multi-entities simulations.
  - This issue was not affecting simulations with several persons in a _single_ entity
  - The underlying `entity.value_from_person` operator was not working as expected in case the persons of the simulation were not sorted by entity id in the persons vector (see example in 22.0.8 right below).

### 22.0.8 [#646](https://github.com/openfisca/openfisca-core/pull/639)

* Fix `entity.max`, `entity.min`, `entity.all` and `entity.reduce` for multi-entities simulations.
  - This issue was not affecting simulations with several persons in a _single_ entity
  - These operators were not working as expected in case the persons of the simulation were not sorted by entity id in the persons vector. For instance:
    - First household: [Alice, Bob]
    - Second household: [Cesar]
    - Persons vector: [Alice, Cesar, Bob]

### 22.0.7 [#639](https://github.com/openfisca/openfisca-core/pull/639)

* Update CircleCI configuration to its v2

### 22.0.6 [#642](https://github.com/openfisca/openfisca-core/pull/642)

* Improve parameters performances

### 22.0.5 [#639](https://github.com/openfisca/openfisca-core/pull/639)

* Update country-template dependency to >= 3.0.0, < 4.0.0

### 22.0.4 [#624](https://github.com/openfisca/openfisca-core/pull/624)

* Technical improvement:
* Details:
  - Make sure ParameterNode:__repr__ generates a valid YAML representation

### 22.0.3 [#635](https://github.com/openfisca/openfisca-core/pull/635)

* Update numpy dependency
* Details:
  - Previously, openfisca-core used features removed on numpy 1.13

### 22.0.2 [#627](https://github.com/openfisca/openfisca-core/pull/627) [#593](https://github.com/openfisca/openfisca-core/pull/593)

- Update openfisca_serve [rst](https://openfisca.org/doc/openfisca-python-api/openfisca_serve.html) documentation
  * Make native gunicorn parameters use in `openfisca serve` obvious and make parameters' format more explicit

### 22.0.1 [#628](https://github.com/openfisca/openfisca-core/pull/628)

- Fix a bug that broke the route `calculate` of the legacy web API since `21.0.2`

# 22.0.0 [#602](https://github.com/openfisca/openfisca-core/pull/602)

#### Breaking changes

- Improve entities projection consistency

Before, there were inconsistencies in the behaviors of projectors:

_For instance, for a simulation that contains 4 persons in 1 household:_

```py
person.household('rent', '2018-02')  # The rent paid by the household of the person.
>>> [800, 800, 800, 800]  # Has the dimension of persons (4)

salaries = person.household.members('salary', '2018-02')
sum_salary = person.household.sum(salaries)  # The sum of the salaries of the person's family
>>> [4000] Has the dimension of household (1)
```


Now, consistency have been enforced for all entities related helpers (`sum`, `min`, `max`, `all`, `any`, `has_role`, etc.)


```py
person.household('rent', '2018-02')  # The rent paid by the household of the person.
>>> [800, 800, 800, 800]  # Has the dimension of persons (4)

salaries = person.household.members('salary')
sum_salary = person.household.sum(salaries)  # The sum of the salaries of the person's family
>>> [4000, 4000, 4000, 4000]  # Has the dimension of persons (4)
```

This is a breaking change, as all the adaptations (such as [this one](https://github.com/openfisca/openfisca-france/blob/18.11.0/openfisca_france/model/prestations/minima_sociaux/rsa.py#L375-L376)) used to overcome these inconsistensies must be removed.

## 21.5.0 [#621](https://github.com/openfisca/openfisca-core/pull/621)

- Introduce:
  - [`person.get_rank(entity, criteria, condition)`](https://github.com/openfisca/openfisca-core/blob/21.4.0/openfisca_core/entities.py#L278-L293)
  - [`entity.value_nth_person(k, array, default)`](https://github.com/openfisca/openfisca-core/blob/21.4.0/openfisca_core/entities.py#L515-L520)

## 21.4.0 [#603](https://github.com/openfisca/openfisca-core/pull/603)

#### New features

- Improve `Tracer`:
  - Make aggregation more efficient
  - Introduce [`tracer.print_trace`](https://openfisca.org/doc/openfisca-python-api/tracer.html#openfisca_core.tracers.Tracer.print_trace)

### 21.3.6 [#616](https://github.com/openfisca/openfisca-core/pull/618)

- Describe `/spec` endpoint in OpenAPI documentation available at `/spec`

### 21.3.5 [#620](https://github.com/openfisca/openfisca-core/pull/620)

* Technical improvement:
* Details:
  - Adapt to version `2.1.0` of Country-Template and version `1.1.3` of Extension-Template.

### 21.3.4 [#604](https://github.com/openfisca/openfisca-core/pull/604)

- Introduce [simulation generator](https://openfisca.org/doc/openfisca-python-api/simulation_generator.html)

### 21.3.3 [#608](https://github.com/openfisca/openfisca-core/pull/608)

- Improve API response time

### 21.3.2 [#617](https://github.com/openfisca/openfisca-core/pull/611)

- Make decompositions more robust

### 21.3.1 [#617](https://github.com/openfisca/openfisca-core/pull/617)

- Fix bug on API `/variable/{id}`
  - Encode API `/variable/{id}` output to `utf-8`
  - Add tests for `/variable/{id}` and `/parameter/{id}` encoding

## 21.3.0 [#610](https://github.com/openfisca/openfisca-core/pull/610)

Add `--only-variables` and `--ignore-variables` options to `openfisca-run-test` to filter out tested output variables if needed.

### 21.2.2 [#612](https://github.com/openfisca/openfisca-core/pull/612)

- When a variable file is loaded twice in the same python interpreter, make sure the second loading doesn't corrupt the first one.
    - This fixes a bug introduced in 21.0.2, which could lead to a corruption of the tax and benefit in rare edge cases

### 21.2.1 [#613](https://github.com/openfisca/openfisca-core/pull/613)

- Fix two bugs that appeared with 21.2.0:
  - Properly encode the result of a formula returning an Enum value
  - Enable storing an Enum value on disk

## 21.2.0 [#601](https://github.com/openfisca/openfisca-core/pull/601)

#### New features

- Improve [`holder.get_memory_usage`]((https://openfisca.org/doc/openfisca-python-api/holder.html#openfisca_core.holders.Holder.get_memory_usage)):
  - Add `nb_requests` and `nb_requests_by_array` fields in the memory usage stats for traced simulations.

- Enable intermediate data storage on disk to avoid memory overflow
  - Introduce `memory_config` option in `Simulation` constructor
    - This allows fine tuning of memory management in OpenFisca

For instance:

```
from openfisca_core.memory_config import MemoryConfig

simulation = ...  # create a Simulation object

config = MemoryConfig(
    max_memory_occupation = 0.95,  # When 95% of the virtual memory is full, switch to disk storage
    priority_variables = ['salary', 'age'],  # Always store these variables in memory
    variables_to_drop = ['age_elder_for_family_benefit']  # Do not store the value of these variables
    )

simulation.memory_config = config
```

## 21.1.0 [#598](https://github.com/openfisca/openfisca-core/pull/598)

#### New features

- Improve `Tracer`:

  - Introduce an `aggregate` option in [`tracer.print_computation_log`](https://openfisca.org/doc/openfisca-python-api/tracer.html#openfisca_core.tracers.Tracer.print_computation_log) to handle large population simulations.
  - Introduce [`tracer.usage_stats`](https://openfisca.org/doc/openfisca-python-api/tracer.html#openfisca_core.tracers.Tracer.usage_stats) to keep track of the number of times a variable is computed.

- Introduce methods to keep track of memory usage:

  - Introduce [`holder.get_memory_usage`](https://openfisca.org/doc/openfisca-python-api/holder.html#openfisca_core.holders.Holder.get_memory_usage)
  - Introduce `entity.get_memory_usage`
  - Introduce `simulation.get_memory_usage`

- Improve `Holder` public interface:

  - Enhance [`holder.delete_arrays`](https://openfisca.org/doc/openfisca-python-api/holder.html#openfisca_core.holders.Holder.get_memory_usage) to be able to remove known values only for a specific period
  - Introduce [`holder.get_known_periods`](https://openfisca.org/doc/openfisca-python-api/holder.html#openfisca_core.holders.Holder.get_known_periods)

- Introduce [`variable.get_formula`](https://openfisca.org/doc/openfisca-python-api/variables.html#openfisca_core.variables.Variable.get_formula)

- Re-introduce `taxscales.combine_tax_scales` to combine several tax scales.

#### Deprecations

- Deprecate `requested_period_added_value` base function, as it had no effect.

### 21.0.3 [#595](https://github.com/openfisca/openfisca-core/pull/595)

#### Bug fix

- Fix API response encoding from ascii to utf-8
  * Improve user message by displaying `UnicodeDecodeError` information

# 21.0.2 [#589](https://github.com/openfisca/openfisca-core/pull/589) [#600](https://github.com/openfisca/openfisca-core/pull/600) [#605](https://github.com/openfisca/openfisca-core/pull/605)

_Note: the 21.0.1 and 21.0.0 versions have been unpublished due to performance issues_

#### Breaking changes

##### Change the way enumerations (Enum) are defined when coding variables

Before:

```py
HOUSING_OCCUPANCY_STATUS = Enum([
    u'Tenant',
    u'Owner',
    u'Free lodger',
    u'Homeless'])
```

Now:

```py
class HousingOccupancyStatus(Enum):
    tenant = u'Tenant'
    owner = u'Owner'
    free_lodger = u'Free lodger'
    homeless = u'Homeless'
```

> Each Enum item has:
> - a `name` property that contains its key (e.g. `tenant`)
> - a `value` property that contains its description (e.g. `"Tenant or lodger who pays a monthly rent"`)

- Enum variables must now have an explicit default value

```py
class housing_occupancy_status(Variable):
    possible_values = HousingOccupancyStatus,
    default_value = HousingOccupancyStatus.tenant
    entity = Household
    definition_period = MONTH
    label = u"Legal housing situation of the household concerning their main residence"
```


- In a formula, to compare an Enum variable to a fixed value, use `housing_occupancy_status == HousingOccupancyStatus.tenant`

- To access a parameter that has a value for each Enum item (e.g. a value for `zone_1`, a value for `zone_2` ... ), use fancy indexing

> For example, if there is an enum:
> ```py
>     class TypesZone(Enum):
>         z1 = "Zone 1"
>         z2 = "Zone 2"
> ```
> And two parameters `parameters.city_tax.z1` and `parameters.city_tax.z2`, they can be dynamically accessed through:
> ```py
> zone = numpy.asarray([TypesZone.z1, TypesZone.z2, TypesZone.z2, TypesZone.z1])
> zone_value = parameters.rate._get_at_instant('2015-01-01').single.owner[zone]
> ```
> returns
> ```py
> [100, 200, 200, 100]
> ```
>

##### Change the simulation inputs and outputs for enumeration variables

###### Web API and YAML tests

- When setting the value of an input Enum variable for a simulation, the user must now send the **string identifier** (e.g. `free_lodger`).
   - The item index (e.g. `2`) is not accepted anymore
   - The value (e.g. `Free lodger`) is not accepted anymore.

- When calculating an Enum variable through the web API, the output will now be the string identifier.

###### Python API

- When using the Python API (`set_input`), the three following inputs are accepted:
   - The enum item (e.g. HousingOccupancyStatus.tenant)
   - The enum string identifier (e.g. "tenant")
   - The enum item index, though this is not recommanded.
     - If you rely on index, make sure to specify an `__order__` attribute to all your enums to make sure each intem has the right index. See the enum34 [doc](https://pypi.python.org/pypi/enum34/1.1.1).

> Example:
```py
holder = simulation.household.get_holder('housing_occupancy_status')
# Three possibilities
holder.set_input(period, numpy.asarray([HousingOccupancyStatus.owner]))
holder.set_input(period, numpy.asarray(['owner']))
holder.set_input(period, numpy.asarray([0])) # Highly not recommanded
```

- When calculating an Enum variable, the output will be an [EnumArray](https://openfisca.org/doc/openfisca-python-api/enum_array.html#module-openfisca_core.indexed_enums).

# 20.0.0 [#590](https://github.com/openfisca/openfisca-core/pull/590)

#### Breaking changes

##### Change the way Variables are declared

- Replace `column` attribute by `value_type`
  * Possible values of `value_type` are:
    * `int`
    * `float`
    * `bool`
    * `str`
    * `date`
    * `Enum`

Before:

```py
class basic_income(Variable):
    column = FloatCol
    entity = Person
    definition_period = MONTH
    label = "Basic income provided to adults"
```

Now:

```py
class basic_income(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    label = "Basic income provided to adults"
```

- `default_value` is now a `Variable` attribute

Before:

```py
class is_citizen(Variable):
    column = BoolCol(default = True)
    entity = Person
    definition_period = MONTH
    label = "Whether the person is a citizen"
```

Now:

```py
class is_citizen(Variable):
    value_type = bool
    default_value = True
    entity = Person
    definition_period = MONTH
    label = "Whether the person is a citizen"
```

- For `Variables` which `value_type` is `str`, `max_lentgh` is now an attribute

Before:

```py
class zipcode(Variable):
    column = FixedStrCol(max_length = 5)
    entity = Menage
    label = u"Code INSEE (depcom) du lieu de résidence"
    definition_period = MONTH
```

After:

```py
class zipcode(Variable):
    value_type = str
    max_length = 5
    entity = Menage
    label = u"Code INSEE (depcom) du lieu de résidence"
    definition_period = MONTH
```

- For `Variables` which `value_type` is `Enum`, `possible_values` is now an attribute:

Before:

```py
class housing_occupancy_status(Variable):
    column = EnumCol(
        enum = Enum([
            u'Tenant',
            u'Owner',
            u'Free lodger',
            u'Homeless'])
        )
    entity = Household
    definition_period = MONTH
    label = u"Legal housing situation of the household concerning their main residence"
```

After:

```py
class housing_occupancy_status(Variable):
    value_type = Enum
    possible_values = Enum([
        u'Tenant',
        u'Owner',
        u'Free lodger',
        u'Homeless'
        ])
    entity = Household
    definition_period = MONTH
    label = u"Legal housing situation of the household concerning their main residence"
```

- Remove `PeriodSizeIndependentIntCol`:
  * Replaced by `Variable` attribute `is_period_size_independent`


##### Deprecate `Column`

`Column` are now considered deprecated. Preferably use `Variable` instead.

If you do need a column for retro-compatibility, you can use:

```py
from openfisca_core.columns import make_column_from_variable

column = make_column_from_variable(variable)
```


- In `TaxBenefitSystem`:
  * Remove `neutralize_column` (deprecated since `9.1.0`, replaced by `neutralize_variable`)
  * Rename `column_by_name` to `variables`
  * Rename `get_column` to `get_variable`
  * Remove `update_column`
  * Remove `add_column`
  * Remove `automatically_loaded_variable` (irrelevant since conversion columns have been removed)
  * Move `VariableNotFound` to `errors` module


- In `Holder`:
  * Rename `holder.column` to `holder.variable`

- In `Column`:
  * `Column` should only be instantiated using `make_column_from_variable`. Former constructors do not work anymore.
  * Remove `column.start`, which was `None` since `14.0.0`
  * Replace `column.formula_class` by `variable.formula`
  * Replace `column.enum` by `variable.possible_values`
  * Replace `column.default` by `variable.default_value`

- In `formulas`:
  * Rename `get_neutralized_column` to `get_neutralized_variable`
  * Remove `new_filled_column`

- In `Variable`:
  * Remove `to_column`
  * Variables can now directly be instanciated:

```py
class salary(Variable):
    entity = Person
    ...


salary_variable = salary()
```

You can learn more about `Variable` by checking its [reference documentation](https://openfisca.org/doc/openfisca-python-api/variables.html).

# 19.0.0 [#583](https://github.com/openfisca/openfisca-core/pull/583)
> Wrongfully published as 18.2.0

#### Breaking changes

- Change the way the API is started
  * The previous command `COUNTRY_PACKAGE=openfisca_country gunicorn ...` does not work anymore
  * The new command to serve the API is `openfisca serve`.
    * Read more in the [doc](https://openfisca.readthedocs.io/en/latest/openfisca_serve.html)
    * This command allows to serve reforms and extensions in the new API

- In `openfisca-run-test` and `openfisca-serve`, rename option `--country_package` to `--country-package`

## 18.1.0 [#578](https://github.com/openfisca/openfisca-core/pull/578)

#### New features

- Improve the representations of parameters when navigating the legislation in Python.

For instance:
```
tax_benefit_system.parameters.benefits

>>> basic_income:
>>>   2015-12-01: 600.0
>>> housing_allowance:
>>>   2016-12-01: None
>>>   2010-01-01: 0.25

tax_benefit_system.parameters.benefits.basic_income

>>>2015-12-01: 600.0
```

- Request parameter at a given date with the `parameters.benefits('2015-07-01')` notation.

- Be more flexible about parameters definitions

The two following expressions are for instance striclty equivalent:

```
Parameter("taxes.rate", {"2015-01-01": 2000})
Parameter("taxes.rate", {"values": {"2015-01-01":{"value": 2000}}})
```

- Make sure `parameters.benefits('2015-07-01')` and `parameters.benefits('2015-07')` return the same value.
- Raise an error when calling `parameters.benefits('invalid_key')`.
- Improve errors when `parameter.update` is used with wrong arguments

#### Deprecations

- Deprecate `ValuesHistory` class. Use `Parameter` instead.
- Deprecate `parameter.values_history`. Just use `parameter` instead.

### 18.0.2 [#585](https://github.com/openfisca/openfisca-core/pull/585)

- Track the real visitor IP in the web API
  - Handle the nginx proxy

### 18.0.1 [#584](https://github.com/openfisca/openfisca-core/pull/584)

- Add a link in `openAPI.yml` to the OpenFisca documentation page explaining the web API inputs and outputs for the /calculate route.

## 18.0.0 [#582](https://github.com/openfisca/openfisca-core/pull/582)

#### New features

Add tracing to get details about all the intermediate calculations of a simulation

- Introduce new Web API route `/trace` to get a simulation's detailed calculation steps
  - See the [swagger documentation for OpenFisca-France](https://legislation.openfisca.fr/swagger)

- Introduce `simulation.tracer.print_computation_log` to print a simulation's detailed calculation steps
  - This is available if the `trace` argument has been set to `True` in the `Simulation` constructor.
  - See the [reference documentation](https://openfisca.readthedocs.io/en/latest/tracer.html) about the tracer.

_Warning: Both of these features are still currently under experimentation. You are very welcome to use them and send us precious feedback, but keep in mind that the way they are used and the results they give might change without any major version bump._

#### Breaking changes

- Deprecate and remove:
  - `simulation.traceback`
  - `simulation.stack_trace`
  - `simulation.find_traceback_step`
  - `simulation.stringify_input_variables_infos`
  - `simulation.stringify_variable_for_period_with_array`

- Remove argument `debug_all` from:
  - `Scenario.new_simulation` method
  - `Simulation` constructor

### 17.2.1 [#581](https://github.com/openfisca/openfisca-core/pull/581)

- Add the possibility to track API visitor's IP

## 17.2.0 [#570](https://github.com/openfisca/openfisca-core/pull/570)

- Enable to calculate parameters according to a variable

For instance, if a parameter `rate` depends on a variable `zone` that can take the values `z1` or `z2`:

In `rate.yaml`:

```
z1:
  values:
    '2015-01-01':
      value: 100
z2:
  values:
    '2015-01-01':
      value: 200
```

Then it is now possible to use:

```
zone = household('zone', period)
rate = parameters(period).rate[zone]
```


For more information, check the [documentation](https://openfisca.org/doc/coding-the-legislation/legislation_parameters.html#computing-a-parameter-that-depends-on-a-variable-fancy-indexing)

### 17.1.2 [#569](https://github.com/openfisca/openfisca-core/pull/569)

- Fix migration script `xml_to_yaml.py`
  - The attributes `reference` of nodes `END`, `VALUE`, `PLACEHOLDER`, `BAREME`, `TRANCHE`, `ASSIETTE`, `TAUX`, `MONTANT`, `SEUIL` were not parsed. Now they are parsed to YAML.

### 17.1.1

- Reference the new address of the documentation

## 17.1.0

- Allow to document entities and entities roles
  - Add attribute `Entity.doc` (e.g. `Household.doc`)
  - Add attribute `Role.doc` (e.g. `Household.CHILD.doc`)

### 17.0.1

#### Minor Change

- Handle the case where the user accidentally puts a coma at the end of a variable reference so it has no consequence on the API output.
- All variable references are transformed into lists of strings.

# 17.0.0 - [#552](https://github.com/openfisca/openfisca-core/pull/552)

#### Breaking changes

##### Parameter files

* Load the legislation parameters from a directory `parameters` containing YAML files, instead of XML files

  Before:
  ```XML
  <NODE code="root">
    <NODE code="impot">
      <CODE code="taux" description="" format="percent">
        <END deb="2016-01-01"/>
        <VALUE deb="2015-01-01" valeur="0.32" />
        <VALUE deb="1998-01-01" valeur="0.3" />
      </CODE>
    </NODE>
  </NODE>
  ```

  Now:
  ```yaml
  impot:
    taux:
      description: Taux d'impôt sur les salaires
      unit: /1
      values:
        2016-01-01:
          value: null
        2015-01-01:
          value: 0.32
        1991-01-01:
          value: 0.3
  ```

  - The XML attributes `format` and `type` are replaced by the YAML attribute `unit`, which is a free text field.

##### reforms

* Rename `Reform.modify_legislation_json()` -> `Reform.modify_parameters()`
* Remove `reforms.compose_reforms()`.
* Remove `reforms.update_legislation()`.
  - To modify an existing parameter, use `ValuesHistory.update()` instead.
  - You can navigate the parameters using `.` (e.g. `parameters.taxes.tax_on_salaries.public_sector.rate`)
  - Before:
    ```python
    new_legislation_parameters = update_legislation(
        legislation_json = original_legislation_parameters,
        path = ('children', 'impot_revenu', 'children', 'bareme', 'brackets', 1, 'threshold'),
        period = reform_period,
        value = 6011,
        )
    ```
  - Now:
    ```python
    parameters.impot_revenu.bareme[1].threshold.update(period = reform_period, value = 6011)
    ```

* Change the syntax to dynamically create new parameters
  - Before :
    ```python
    reform_legislation_subtree = {
        "@type": "Node",
        "description": "PLF 2016 sur revenus 2015",
        "children": {
            "decote_seuil_celib": {
                "@type": "Parameter",
                "description": "Seuil de la décôte pour un célibataire",
                "format": "integer",
                "unit": "currency",
                "values": [
                    {'start': u'2016-01-01', },
                    {'start': u'2015-01-01', 'value': round(1135 * (1 + inflation))},
                    ],
                },
            "decote_seuil_couple": {
                "@type": "Parameter",
                "description": "Seuil de la décôte pour un couple",
                "format": "integer",
                "unit": "currency",
                "values": [
                    {'start': u'2065-01-01', },
                    {'start': u'2015-01-01', 'value': round(1870 * (1 + inflation))},
                    ],
                },
            },
        }
    reference_legislation_copy['children']['plf2016_conterfactual'] = reform_legislation_subtree
    ```

  - Now:
    ```python
    from openfisca_core.parameters import ParameterNode

    inflation = .001
    reform_parameters_subtree = ParameterNode('plf2016_conterfactual', data = {
        'decote_seuil_celib': {
          'values': {
            "2015-01-01": {'value': round(1135 * (1 + inflation))},
            "2016-01-01": {'value': None}
            }
          },
        'decote_seuil_couple': {
          'values': {
            "2015-01-01": {'value': round(1870 * (1 + inflation))},
            "2065-01-01": {'value': None}
            }
          },
        })
    reference_parameters.add_child('plf2016_conterfactual', reform_parameters_subtree)
    ```

  - Note that this way of creating parameters is only recommanded when using dynamically computed values (for instance `round(1135 * (1 + inflation))` in the previous example). If the values are static, the new parameters can be directly built from YAML (See New features section).

##### TaxBenefitSystem

* Remove parameter `legislation_json` in constructor
* Remove methods/attributes:
  - `compact_legislation_by_instant_cache`
  - `get_baseline_compact_legislation`
  - `compute_legislation`
  - `get_legislation`
    + We can now directly use the `parameters` attribute.
* Rename
  - `preprocess_legislation` -> `preprocess_parameters`
  - `add_legislation_params` -> `load_parameters`
  - `get_compact_legislation` -> `get_parameters_at_instant`
    + The signature of the method has changed. Check the [documentation](https://openfisca.org/doc/openfisca-python-api/tax-benefit-system.html#openfisca_core.taxbenefitsystems.TaxBenefitSystem.load_parameters).

##### Simulation

* Remove methods/attributes:
  - `compact_legislation_by_instant_cache`
  - `get_baseline_compact_legislation`
* Rename
    `baseline_compact_legislation_by_instant_cache` -> `baseline_parameters_at_instant_cache`
    `legislation_at` -> `parameters_at`

#### New features

* In reforms, new parameters can be added from a YAML file.
  - The function `parameters.load_parameter_file()` loads a YAML file.
  - The function `ParameterNode.add_child()` adds a new child to an existing legislation node.
  - Example:
    ```python
    import os
    from openfisca_core.parameters import load_parameter_file

    dir_path = os.path.dirname(__file__)

    def reform_modify_parameters(parameters):
        file_path = os.path.join(dir_path, 'plf2016.yaml')
        reform_parameters_subtree = load_parameter_file(name = 'plf2016', file_path=file_path)
        parameters.add_child('plf2016', reform_parameters_subtree)
        return parameters

    ...
    ```

* In module model_api, add classes that are needed to build reforms:
  - `load_parameter_file`
  - `ParameterNodeNode`
  - `Scale`
  - `Bracket`
  - `Parameter`
  - `ValuesHistory`
  - `periods.period`.


#### Technical changes

* Refactor the internal representation and the interface of legislation parameters
  - The parameters of a legislation are wraped into the classes `Node`, `Parameter`, `Scale`, `Bracket`, `ValuesHistory`, `ValueAtInstant` instead of bare python dict.
  - The parameters of a legislation at a given instant are wraped into the classes `NodeAtInstant`, `ValueAtInstant` and tax scales instead of bare python objects.
  - The file `parameters.py` and the classes defined inside are responsible both for loading and accessing the parameters. Before the loading was implemented in `legislationsxml.py` and the other processings were implemented in `legislations.py`
  - The validation of the XML files was performed against a XML schema defined in `legislation.xsd`. Now the YAML files are loaded with the library `yaml` and then validated in basic Python.

* The word "legislation" is replaced by the word "parameters" in several internal variables and internal methods. It Reduced the ambiguity between the legislation as a tax and benefit system and the legislation as the parameters.
  - `TaxBenefitSystem.compact_legislation_by_instant_cache` -> `TaxBenefitSystem._parameters_at_instant_cache`
  - `TaxBenefitSystem.get_baseline_compact_legislation()` -> `TaxBenefitSystem._get_baseline_parameters_at_instant()`
  - `Simulation.compact_legislation_by_instant_cache` -> `Simulation._parameters_at_instant_cache`
  - `Simulation.get_compact_legislation()` -> `Simulation._get_parameters_at_instant()`
  - `Simulation.get_baseline_compact_legislation()` -> `Simulation._get_baseline_parameters_at_instant()`

* The optionnal parameter `traced_simulation` is removed in function `TaxBenefitSystem.get_compact_legislation()` (now `TaxBenefitSystem.get_parameters_at_instant()`). This parameter had no effect.

* The optional parameter `with_source_file_infos` is removed in functions `TaxBenefitSystem.compute_legislation()` (now `TaxBenefitSystem._compute_parameters()`) and `TaxBenefitSystem.get_legislation()`. This parameter had no effect.

* In the API preview, update the internal transformation of the parameters.

* In the directory `script`, add a subdirectory `migrations`.

## 16.3.0

- Support `reference` attributes on all parameter XML nodes.
  - You can now add a `reference` on a `<VALUE>`, for example.

## 16.2.0

In the preview web API, for variables of type `Enum`:

* Accept and recommend to use strings as simulation inputs, instead of the enum indices.
  - For instance, `{"housing_occupancy_status": {"2017-01": "Tenant"}}` is now accepted and prefered to `{"housing_occupancy_status": {"2017-01": 0}}`).
  - Using the enum indices as inputs is _still accepted_ for backward compatibility, but _should not_ be encouraged.
* Return strings instead of enum indices.
  - For instance, is `housing_occupancy_status` is calculated for `2017-01`, `{"housing_occupancy_status": {"2017-01": "Tenant"}}` is now returned, instead of `{"housing_occupancy_status": {"2017-01": 0}}`.
* In the `/variable/<variable_name>` route, document possible values.
* In the Open API specification, document possible values following JSON schema.
* In the `/variable/<variable_name>` route:
  - Document possible values
  - Use a string as a default value (instead of the enum default indice)
* In the Open API specification, document possible values following JSON schema.

### 16.1.1

#### Minor Change

* Enhance logs
    - Replace prints by proper logs
    - Give clear and concise feedback to users when a formula cannot compute.

## 16.1.0

* Enable API monitoring with Piwik
  - See the [documentation](https://github.com/openfisca/openfisca-core/#tracker)

# 16.0.0

#### Breaking changes - [#545](https://github.com/openfisca/openfisca-core/pull/545)

* Deprecate `parsers`
  - They can no longer be installed through `pip install openfisca_core[parsers]`
  - They can still install them directly with `pip install openfisca_parsers`, but they won't be maintained.

### 15.0.1 - [#538](https://github.com/openfisca/openfisca-core/pull/538)

#### Bug fix

- Make `missing_value` base function compatible with v4 syntax and extra params

# 15.0.0

#### Breaking changes - [#525](https://github.com/openfisca/openfisca-core/pull/525)

* Rename `Variable` attribute `url` to `reference`
  - This attribute is the legislative reference of a variable.
  - As previously, this attribute can be a string, or a list of strings.
* Rename `Variable` attribute `reference` to `baseline_variable`
  - This attibute is, for a variable defined in a reform, the baseline variable the reform variable is replacing.
* Remove variable attribute `law_reference`
* Rename `TaxBenefitSystem.reference` to `TaxBenefitSystem.baseline`
* Rename `TaxBenefitSystem.get_reference_compact_legislation` to `TaxBenefitSystem.get_baseline_compact_legislation`
* Rename `Simulation.reference_compact_legislation_by_instant_cache` to `Simulation.baseline_compact_legislation_by_instant_cache`
* Rename `Simulation.get_reference_compact_legislation` to `Simulation.get_baseline_compact_legislation`
* Rename parameter `reference` of `AbstractScenario.new_simulation()` to `use_baseline`
* Rename parameter `reference` of `Simulation.legislation_at()` to `use_baseline`

### 14.1.4 - [#539](https://github.com/openfisca/openfisca-core/pull/539)

#### New features

- In the preview API `/calculate` route
  - Handle roles with no plural
  - Force all persons to be allocated to all entities
  - Improve error messages
  - Detect unexpected entity errors first
- Document new simulation and entities constructors.

### 14.1.3 - [#541](https://github.com/openfisca/openfisca-core/pull/541)

#### Minor Change

- Rewrite `/calculate` example in the Open API spec so that it works for `Openfisca-France`

### 14.1.2 - [#535](https://github.com/openfisca/openfisca-core/pull/535)

#### Bug fix

- Fix `formula.graph_parameters` and `formula.to_json`
  - Bugs were introduced in `14.0.0`

- Fix `simulation.graph`
  - A bug was introduced in `14.1.0`

### 14.1.1 - [#533](https://github.com/openfisca/openfisca-core/pull/533)

#### Bug fix

- Fix `simulation.clone` and `entity.clone` methods.
  - A bug was introduced in `14.1.0`

## 14.1.0 - [#528](https://github.com/openfisca/openfisca-core/pull/528)

#### New features

- Introduce `/calculate` route in the preview API
  - Allows to run calculations.
  - Takes a simulation `JSON` as an input, and returns a copy of the input extended with calculation results.

- Handle `500` errors in the preview API
    - In this case, the API returns a JSON with details about the error.

- Allows simulations to be built from a JSON using their constructor
  - For instance `Simulation(simulation_json = {"persons": {...}, "households": {...}}, tax_benefit_system = tax_benefit_system)`

- Allows entities to be built from a JSON using their constructor
  - For instance `Household(simulation, {"first_household": {...}})`

- Introduce `tax_benefit_system.get_variables(entity = None)`
  - Allows to get all variables contained in a tax and benefit system, with filtering by entity

#### Deprecations

- Deprecate `simulation.holder_by_name`, `simulation.get_holder`, `get_or_new_holder`
  - These functionalities are now provided by `entity.get_holder(name)`

- Deprecate constructor `Holder(simulation, column)`
  - A `Holder` should now be instanciated with `Holder(entity = entity, column = column)`

### 14.0.1 - [#527](https://github.com/openfisca/openfisca-core/pull/527)

* Improve error message and add stack trace when a module import fails

# 14.0.0 - [#522](https://github.com/openfisca/openfisca-core/pull/522)

#### Breaking changes

- In variables:
  - Merge `Variable` and `DatedVariable`.
    - `Variable` can now handle formula evolution over time.
  - Remove `start_date` attribute
  - Rename `stop_date` attribute to `end`
    - Introduce end string format `end = 'YYYY-MM-DD'`
- In formulas:
  - Merge `SimpleFormula` and `DatedFormula`.
    - `Formula` evolves over time.
  - Remove `@dated_function`
    - start definition goes to formula name: `formula_YYYY[_MM[_DD]]`
    - stop is deduced from next formula start

  Before:
  ```
  class your_variable(DatedVariable):
      # ... attributes
      start_date = datetime.date(2015, 05, 01)
      stop_date = datetime.date(2017, 05, 31)

      # openfisca chooses most restrictive start in (start_date, @dated_function start)
      @dated_function(start = date(2015, 1, 1), stop = date(2016, 12, 31))
      def function_2015_something(self, simulation, period):
          # Calculate for 2015

      @dated_function(start = date(2016, 1, 1))
      def function__different_name(self, simulation, period):
          # Calculate for 2016 > 2017-05-31 (including 2017-05-31 stop_date day)
  ```
  After:
  ```
  class your_variable(Variable):
      # ... unchanged attributes
      end = '2017-05-31'  # string format 'YYYY-MM-DD'

      # name should begin with 'formula' / you define the start in the name
      def formula_2015_05_01(self, simulation, period):  # stops on last day before next formula
          # Calculate for 2015

      def formula_2016(self, simulation, period):  # similar to formula_2016_01_01 or formula_2016_01
          # Calculate for 2016+ > 2017-05-31 (including 2017-05-31 end day)
  ```

#### New features

- Change `ETERNITY` period effect
  - Remove restriction that prevented formula changes over time for a variable with `definition_period = ETERNITY`.

### 13.0.1 - [#526](https://github.com/openfisca/openfisca-core/pull/526)

### Bug fix

* Require numpy < 1.13.
  - Openfisca is not yet compatible with the new numpy version 1.13.

# 13.0.0

#### Breaking changes

* Disallow text out of tags in XML parameters
  - This prevents to add "comments" that would be lost by automated transformation of these parameters.

#### New features

* Introduce a "reference" attribute to document a source in XML parameters

## 12.3.0

* Serve the [OpenAPI specification](https://www.openapis.org/) under the API route `/spec/`

## 12.2.0

* Use `nose` in the `openfisca-run-test` script
  - This avoids boilerplate code on country packages, and makes parallelism easier to set on Circle CI.

### 12.1.4

* Fix package naming conflict between the preview API and the official one.
* Fix import error

### 12.1.3

* Validate XML parameters with lxml and a XML Schema
* Raise nicer errors during validation

### 12.1.2

* Improve the error when the period argument is forgotten in entity call

### 12.1.1

* When replacing a variable by another one in a reform, assume the new variable has the same metadata than the reference one.
  - The is currently the behaviour for all other metadata.

## 12.1.0

* Include the preview API into OpenFisca-Core
* Remove internationalization (`i18n`, `Babel`)
* Use CircleCI instead of Travis

### 12.0.3

* Fix variable `source_file_path` computation.
  - Make sure the tax and benefit system `location` metadata is consistent with the actual python files being loaded.

### 12.0.2

* Fix a bug introduced by 11.0.0: variables with several references could not be loaded.

### 12.0.1

* Fix a bug introduced by 12.0.0: the description of a parameter node was no longer exported in the parameter JSON.

# 12.0.0

#### Breaking changes

* Deprecate and remove the `fin` attribute in XML parameters.
  - The end date of a parameter is assumed to be the start of the next one.
  - The `<END>` indicates that a parameter does not exist anymore
* Deprecate and remove the `fuzzy` attribute in XML parameters.
  - By construction, the value of a parameter is always extended towards the future.
  - To indicate a likely change of the legislation, a `<PLACEHOLDER>` can be added.
* Deprecate and remove `reforms.create_item`
  - New items are created directly with the method `reforms.update_items`.
* Deprecate and remove `reforms.split_item_containing_instant`
  - Splitting items does not make sense in the new convention. Use `reform.update_items` to update the parameters.

# 11.0.0

#### Breaking changes

These breaking changes only concern variable and tax and benefit system **metadata**. They **do not** impact calculations.

* Make `tax_benefit_system.get_package_metadata()` return a `dict` instead of a `tuple`
* Make `column.source_file_path` a relative path (was absolute before)
* Make `column.url` a list instead of a string

#### New features

* Make `tax_benefit_system.get_package_metadata()` more robust
  - Handle reforms
  - Handle tax and benefit systems that are not defined within a package and/or a distribution

#### Technical changes

* Turn `Variable`s with a `start_date` and/or a `stop_date` into `DatedVariable`s
  - This is transparent for users.

### 10.0.2

* Do not cache values for neutralized variables
  - To reduce memory usage for large population simulations

### 10.0.1

* Improve the raised error message when a wrong period type is given as an input

# 10.0.0

#### Breaking changes

* In YAML tests:
  - Deprecate and remove the `IGNORE_` prefix
  - Deprecate and remove the `ignore` property
* In the YAML test runner:
  - Deprecate and remove the `force` option (`-f` in the shell script)
  - Deprecate and remove the `default_absolute_error_margin` option (`-M` in the shell script)
  - Deprecate and remove the `default_relative_error_margin` option (`-m` in the shell script)

#### New features

* Add `Reform` and `numpy.round` (as `round_`) in the model API
* Introduce `tax_benefit_system.apply_reform(reform_path)`
* Allow YAML tests to declare the reforms they need to be executed (through the `reforms` property)

#### Technical changes

* Move the `dummy_extension` to `OpenFisca-Dummy-Country`
* Test `openfisca-run-test` script

## 9.1.0

* Rename `neutralize_column` to `neutralize_variable`
  - Deprecate `neutralize_column` without removing it
* Document `neutralize_variable`

### 9.0.2

* Fix spelling in error messages

### 9.0.1

* Test marginal scales
* Move tests out of the main package
* These changes are transparent for users

# 9.0.0

* Make sure identic periods are stringified the same way
* _Breaking changes_:
  - Change `periods.period` signature.
    - It now only accepts strings.
  - Restrict the possible inputs for `periods.period`
    - The authorized formats are listed in [the doc](https://openfisca.org/doc/key-concepts/periodsinstants.html)
  - Deprecate and remove:
    - `periods.json_or_python_to_period`
    - `periods.make_json_or_python_to_period`

### 8.0.1

* Move the dummy country to [its own repository](https://github.com/openfisca/openfisca-dummy-country)

# 8.0.0

* Raise more explicit error when an invalid test case is given
* Raise more friendly error when trying to calculate a variable which doesn't exist
* _Breaking change_: Python exceptions will now be raised when the test case in invalid. Before, only a byriani error was returned. Reusers must therefore adapt their exception handling.

## 7.1.0

* Add `Entity.to_json` method. Used by OpenFisca-Web-API in `/entity` endpoint in particular.

### 7.0.1

* Declare `Openfisca-Parsers` as an optional dependency of `Openfisca-Core`.

# 7.0.0

* Make it mandatory to provide a period when calculating a variable.
  - When a computation is requested (with *.calculate_output, entities.__call__, *.calculate[_add|_divide], *.compute[_add|_divide]), the argument `period` is no longer optional.
  - Previously, the period of the simulation was used instead of a missing period. It was error-prone, as values would be returned for the wrong period, without any error or warning to alert the formula writer about a likely coding error.

## 6.1.0

* Move `base.py` content (file usually located in country packages) to core module `formula_toolbox` so that it can be reused by all countries
* Use `AbstractScenario` if no custom scenario is defined for a tax and benefit sytem

# 6.0.0

#### Breaking changes

* Add **mandatory** attribute `definition_period` to variables
* Enforce that inputs provided for a variable match the variable `definition_period`
  - If a `set_input` attribute has been defined, automatically cast the input accordingly.
* Change the expected output of a formula
  - Only `result` must be returned, instead of `period, result`
* Deprecate and remove:
  - `simulation.print_trace`
  - `simulation.calculate_add_divide` and `simulation.compute_add_divide`
  - `last_duration_last_value` base function
  - `variables_name_to_skip` and `use_set_input_hooks` parameters in `scenario.fill_simulation`
  - `holders.new_test_case_array`
* Deprecate and forbid `dated_holder.array = ...`
* Raise an error when inconsistent year and month inputs provided for a variable
  - Before, the year value would be silently ignored.
* Rename `period.this_month` to `period.first_month`

#### Technical changes

* Make sure the cache only store values for periods matching the variable `definition_period`
* Use a cache buffer in simulation initialisation when axes are used, to avoid `set_input` conflicts
* Make `DatedHolder` only a wrapper of a variable value for a given period, and no more a dated view of a `Holder`

#### Documentation

* the attribute `definition_period` is documented here : https://openfisca.org/doc/coding-the-legislation/35_periods.html

### 5.0.2

* Add `TaxBenefitSystem` doc to the reference doc
  - This is transparent for all users

### 5.0.1

* Improve `openfisca-run-test` script
  - Make country package detection more robust (it only worked for packages installed in editable mode)
  - Use spaces instead of commas as separator in the script arguments when loading several extensions or reforms (this is more standard)
* Refactor the `scripts` module to seperate the logic specific to yaml test running from the one that can be re-used by any script which needs to build a tax and benefit system.

# 5.0.0

* Move `json_or_python_to_test_case` from country packages to core
* Breaking change: `scenarios.set_entities_json_id` has been moved, and should not be considered a public function.

### 4.3.6

* Bug fix : handle the case when CompactNode.name is None.

### 4.3.5

* Refactor decomposition TaxBenefitSystem attributes. Reform inherit the decomposition_file_path from the reference TaxBenefitSystem.
  This does not require changing anything from the caller, which should use the `decompositions.get_decomposition_json` function instead of those attributes.

### 4.3.4

* Fix occasionnal `NaN` creation in `MarginalRateTaxScale.calc` resulting from `0 * numpy.inf`

### 4.3.3

* Use the actual TaxBenefitSystem and not its reference when neutralizing a column.

### 4.3.2

* Fix `to_value_json` for `DatedVariable` with extra parameters.

This was causing a crash when calculating intermediate variables with the API.

Unlike simple formulas, a `DatedVariable` have several functions. We thus need to select the right one according to the period before doing parameters introspection.

### 4.3.1

* Fix `set_input` and `default` setting in `new_filled_column`

## 4.3.0

* Add reference documentation

### 4.2.1

* Fix permanent and period size independent variables neutralization

## 4.2.0

* Introduce a YAML test runner in openfisca_core
  - Introduce command line tool `openfisca-run-test`

* Refactor the dummy tax benefit system included in openfisca-core
  - Make the dummy country look like a real one
  - Split defining the country from testing

### 4.1.7

* Improve docstring of `MarginalTaxRate.inverse` and add test

### 4.1.6

* Decrease verbosity of `combine_tax_scales`

### 4.1.5

* Enable `extra_params` in formulas with new syntax.

### 4.1.4-Beta

* Fixup 4.1.2:
  * When building positions, handle cases where persons belonging to an entity are not grouped by entity in the persons array.

### 4.1.3-Beta

* Fix bug in entity.sum

### 4.1.2-Beta

* Enable simulation initialization with only legacy roles
  * New roles are in this case automatically infered
  * Positions are always infered from persons entity id

### 4.1.1-Beta

* Fix update_legislation in reforms

### 4.1.0-Beta

* Add `conflicts` and `origin` fields to xml params (needed for baremes IPP importation)

### 4.0.0-Beta

  * Refactor formula syntax

    - Don't use the object simulation in formula writing. The entity the variable is calculated for is now the first argument of the formula, for instance `person` or `family`.

    - The `legislation` is now the (optional) third argument of a formula. It is a function that can be called with a period (or an instant) for argument, and will compute the legislation at `period.start`.

    -  Don't use `calculate_add` and equivalents. Instead, `add` and `divide` are just given in the `options` argument, for instance `options = [ADD]`.

    - Rename `entity_class` to `entity`.

    - Don't explicitly use a `calculate` method, but the `person('salary', period)` notation instead.

  * Introduce implicit conversions between entities, and improve aggregations formulas.

  * Deprecate PersonToEntityColumn and EntityToPersonColumn

  * Change the way entities are declared

  More information on https://github.com/openfisca/openfisca-core/pull/415

## 3.1.0

* Add a `DeprecationWarning` when using a `DateCol` with no `default`, but keep the default date to 1970-01-01.
* Enforce `DateCol.default` to be a `date`.

### 3.0.3

* Fix `cerfa_field` validation in `Column`, `Formula` and `AbstractConversionVariable`.
  Previously, some variables having `cerfa_field` as a `dict` were converted to `unicode` by mistake.
  See https://github.com/openfisca/openfisca-france/issues/543

### 3.0.2

* Move `calmar.py` to [OpenFisca-Survey-Manager](https://github.com/openfisca/openfisca-survey-manager).

  No incidence on users since it was only needed for dataframes.

### 3.0.1

* Adapt requested_period_last_value and last_duration_last_value to extra params

# 3.0.0

* Update introspection data. This allows to enhance data served by the web API which itself feeds the Legislation Explorer.

### 2.2.2

* Update travis procedures

### 2.2.1

* Remove conda from travis config

## 2.2.0

* Implement simulation.calculate `print_trace=True` argument. Options: `max_depth` and `show_default_values`

  Examples:
  ```python
  simulation = scenario.new_simulation(trace=True)
  simulation.calculate('irpp', 2014, print_trace=True)
  simulation.calculate('irpp', 2014, print_trace=True, max_depth=-1)
  simulation.calculate('irpp', 2014, print_trace=True, max_depth=-1, show_default_values=False)
  ```

## 2.1.0 – [diff](https://github.com/openfisca/openfisca-core/compare/2.0.3...2.0.4)

* Load extensions from pip packages

### 2.0.4 – [diff](https://github.com/openfisca/openfisca-core/compare/2.0.3...2.0.4)

* Use DEFAULT_DECOMP_FILE attribute from reference TB system

### 2.0.3 – [diff](https://github.com/openfisca/openfisca-core/compare/2.0.2...2.0.3)

* Explicit the error when a variable is not found

### 2.0.2 – [diff](https://github.com/openfisca/openfisca-core/compare/2.0.1...2.0.2)

* Update numpy dependency to 1.11

### 2.0.1 – [diff](https://github.com/openfisca/openfisca-core/compare/2.0.0...2.0.1)

* Force updating version number and CHANGELOG.md before merging on master
* Release tag and Pip version automatically

# 2.0.0 – [diff](https://github.com/openfisca/openfisca-core/compare/1.1.0...2.0.0)

* Variables are not added to the TaxBenefitSystem when the entities class are imported, but explicitely when the TaxBenefitSystem is instanciated.
  * Metaclasses are not used anymore.
* New API for TaxBenefitSystem
  * Columns are now stored in the TaxBenefitSystem, not in entities.
* New API for rerforms.
* XmlBasedTaxBenefitSystem is deprecated, and MultipleXmlBasedTaxBenefitSystem renamed to TaxBenefitSystem

## 1.1.0 – [diff](https://github.com/openfisca/openfisca-core/compare/1.0.0...1.1.0)

* Implement cache opt out system

# 1.0.0 – [diff](https://github.com/openfisca/openfisca-core/compare/0.5.4...1.0.0)

* Remove `build_column` obsolete function. Use `Variable` class instead.

## 0.5.4 – [diff](https://github.com/openfisca/openfisca-core/compare/0.5.3...0.5.4)

* Merge pull request #382 from openfisca/fix-sum-by-entity
* The result size must be the targent entity'one

## 0.5.3 – [diff](https://github.com/openfisca/openfisca-core/compare/0.5.2...0.5.3)

* Many updates

## 0.5.2 – [diff](https://github.com/openfisca/openfisca-core/compare/0.5.1...0.5.2)

* Add trim option to marginal rate computation
* Compute stop date of whole tax scale instead of a single bracket.
* Use bracket stop date instead of legislation stop date inside a bracket.
* Introduce reference periods
* Fix roles_count bug : was set to 1 for scenarios vectorially defined

## 0.5.1 – [diff](https://github.com/openfisca/openfisca-core/compare/0.5.0...0.5.1)

* Move docs to gitbook repo
* Upgrade to new Travis infrastructure
* Enhance errors display when a reform modifies the legislation

## 0.5.0

* First release uploaded to PyPI
