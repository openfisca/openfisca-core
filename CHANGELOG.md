# Changelog

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
