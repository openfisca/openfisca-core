# Changelog

## 3.1.1

  * Use reference decompositons directory and files when compute decomposition for a refomed tax-benefit-system

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
