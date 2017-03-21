# Changelog

## 9.0.0

* Make sure identic periods are stringified the same way
* _Breaking changes_:
  - Change `periods.period` signature.
    - It now only accepts strings.
  - Restrict the possible inputs for `periods.period`
    - The authorized formats are listed in [the doc](https://doc.openfisca.fr/periodsinstants.html)
  - Deprecate and remove:
    - `periods.json_or_python_to_period`
    - `periods.make_json_or_python_to_period`

## 8.0.1

* Move the dummy country to [its own repository](https://github.com/openfisca/openfisca-dummy-country)

## 8.0.0

* Raise more explicit error when an invalid test case is given
* Raise more friendly error when trying to calculate a variable which doesn't exist
* _Breaking change_: Python exceptions will now be raised when the test case in invalid. Before, only a byriani error was returned. Reusers must therefore adapt their exception handling. 

## 7.1.0

* Add `Entity.to_json` method. Used by OpenFisca-Web-API in `/entity` endpoint in particular.

## 7.0.1

* Declare `Openfisca-Parsers` as an optional dependency of `Openfisca-Core`.

## 7.0.0

* Make it mandatory to provide a period when calculating a variable.
  - When a computation is requested (with *.calculate_output, entities.__call__, *.calculate[_add|_divide], *.compute[_add|_divide]), the argument `period` is no longer optional.
  - Previously, the period of the simulation was used instead of a missing period. It was error-prone, as values would be returned for the wrong period, without any error or warning to alert the formula writer about a likely coding error.

## 6.1.0

* Move `base.py` content (file usually located in country packages) to core module `formula_toolbox` so that it can be reused by all countries
* Use `AbstractScenario` if no custom scenario is defined for a tax and benefit sytem

## 6.0.0

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

* the attribute `definition_period` is documented here : https://doc.openfisca.fr/coding-the-legislation/35_periods.html

## 5.0.2

* Add `TaxBenefitSystem` doc to the reference doc
  - This is transparent for all users

## 5.0.1

* Improve `openfisca-run-test` script
  - Make country package detection more robust (it only worked for packages installed in editable mode)
  - Use spaces instead of commas as separator in the script arguments when loading several extensions or reforms (this is more standard)
* Refactor the `scripts` module to seperate the logic specific to yaml test running from the one that can be re-used by any script which needs to build a tax and benefit system.

## 5.0.0

* Move `json_or_python_to_test_case` from country packages to core
* Breaking change: `scenarios.set_entities_json_id` has been moved, and should not be considered a public function.

## 4.3.6

* Bug fix : handle the case when CompactNode.name is None.

## 4.3.5

* Refactor decomposition TaxBenefitSystem attributes. Reform inherit the decomposition_file_path from the reference TaxBenefitSystem.
  This does not require changing anything from the caller, which should use the `decompositions.get_decomposition_json` function instead of those attributes.

## 4.3.4

* Fix occasionnal `NaN` creation in `MarginalRateTaxScale.calc` resulting from `0 * np.inf`

## 4.3.3

* Use the actual TaxBenefitSystem and not its reference when neutralizing a column.

## 4.3.2

* Fix `to_value_json` for `DatedVariable` with extra parameters.

This was causing a crash when calculating intermediate variables with the API.

Unlike simple formulas, a `DatedVariable` have several functions. We thus need to select the right one according to the period before doing parameters introspection.

## 4.3.1

* Fix `set_input` and `default` setting in `new_filled_column`

## 4.3.0

* Add reference documentation

## 4.2.1

* Fix permanent and period size independent variables neutralization

## 4.2.0

* Introduce a YAML test runner in openfisca_core
  - Introduce command line tool `openfisca-run-test`

* Refactor the dummy tax benefit system included in openfisca-core
  - Make the dummy country look like a real one
  - Split defining the country from testing

## 4.1.7

* Improve docstring of `MarginalTaxRate.inverse` and add test

## 4.1.6

* Decrease verbosity of `combine_tax_scales`

## 4.1.5

* Enable `extra_params` in formulas with new syntax.

## 4.1.4-Beta

* Fixup 4.1.2:
  * When building positions, handle cases where persons belonging to an entity are not grouped by entity in the persons array.

## 4.1.3-Beta

* Fix bug in entity.sum

## 4.1.2-Beta

* Enable simulation initialization with only legacy roles
  * New roles are in this case automatically infered
  * Positions are always infered from persons entity id

## 4.1.1-Beta

* Fix update_legislation in reforms

## 4.1.0-Beta

* Add `conflicts` and `origin` fields to xml params (needed for baremes IPP importation)

## 4.0.0-Beta

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

## 3.0.3

* Fix `cerfa_field` validation in `Column`, `Formula` and `AbstractConversionVariable`.
  Previously, some variables having `cerfa_field` as a `dict` were converted to `unicode` by mistake.
  See https://github.com/openfisca/openfisca-france/issues/543

## 3.0.2

* Move `calmar.py` to [OpenFisca-Survey-Manager](https://github.com/openfisca/openfisca-survey-manager).

  No incidence on users since it was only needed for dataframes.

## 3.0.1

* Adapt requested_period_last_value and last_duration_last_value to extra params

## 3.0.0

* Update introspection data. This allows to enhance data served by the web API which itself feeds the Legislation Explorer.

## 2.2.2

* Update travis procedures

## 2.2.1

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

## 2.0.4 – [diff](https://github.com/openfisca/openfisca-core/compare/2.0.3...2.0.4)

* Use DEFAULT_DECOMP_FILE attribute from reference TB system

## 2.0.3 – [diff](https://github.com/openfisca/openfisca-core/compare/2.0.2...2.0.3)

* Explicit the error when a variable is not found

## 2.0.2 – [diff](https://github.com/openfisca/openfisca-core/compare/2.0.1...2.0.2)

* Update numpy dependency to 1.11

## 2.0.1 – [diff](https://github.com/openfisca/openfisca-core/compare/2.0.0...2.0.1)

* Force updating version number and CHANGELOG.md before merging on master
* Release tag and Pip version automatically

## 2.0.0 – [diff](https://github.com/openfisca/openfisca-core/compare/1.1.0...2.0.0)

* Variables are not added to the TaxBenefitSystem when the entities class are imported, but explicitely when the TaxBenefitSystem is instanciated.
  * Metaclasses are not used anymore.
* New API for TaxBenefitSystem
  * Columns are now stored in the TaxBenefitSystem, not in entities.
* New API for rerforms.
* XmlBasedTaxBenefitSystem is deprecated, and MultipleXmlBasedTaxBenefitSystem renamed to TaxBenefitSystem

## 1.1.0 – [diff](https://github.com/openfisca/openfisca-core/compare/1.0.0...1.1.0)

* Implement cache opt out system

## 1.0.0 – [diff](https://github.com/openfisca/openfisca-core/compare/0.5.4...1.0.0)

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
