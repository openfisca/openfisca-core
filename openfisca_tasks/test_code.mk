## The openfisca command module.
openfisca = openfisca_core.scripts.openfisca_command

## The path to the templates' tests.
ifeq ($(OS),Windows_NT)
	tests = $(shell python -c "import os, $(1); print(repr(os.path.join($(1).__path__[0], 'tests')))")
else
	tests = $(shell python -c "import $(1); print($(1).__path__[0])")/tests
endif

## Run all tasks required for testing.
install: install-deps install-edit install-test

## Enable regression testing with template repositories.
install-test:
	@$(call print_help,$@:)
	@python -m pip install --upgrade --no-deps openfisca-country-template
	@python -m pip install --upgrade --no-deps openfisca-extension-template

## Run openfisca-core & country/extension template tests.
test-code: test-core test-country test-extension
	@##	Usage:
	@##
	@##		make test [pytest_args="--ARG"] [openfisca_args="--ARG"]
	@##
	@##	Examples:
	@##
	@##		make test
	@##		make test pytest_args="--exitfirst"
	@##		make test openfisca_args="--performance"
	@##		make test pytest_args="--exitfirst" openfisca_args="--performance"
	@##
	@$(call print_pass,$@:)

## Run openfisca-core tests.
test-core: $(shell git ls-files "*test_*.py")
	@$(call print_help,$@:)
	@python -m pytest --capture=no \
		openfisca_core/commons \
		openfisca_core/data_storage \
		openfisca_core/entities \
		openfisca_core/holders \
		openfisca_core/indexed_enums \
		openfisca_core/periods \
		openfisca_core/projectors
	@PYTEST_ADDOPTS="$${PYTEST_ADDOPTS} ${pytest_args}" \
		python -m coverage run -m ${openfisca} test \
		$? \
		${openfisca_args}
	@$(call print_pass,$@:)

## Run country-template tests.
test-country:
	@$(call print_help,$@:)
	@PYTEST_ADDOPTS="$${PYTEST_ADDOPTS} ${pytest_args}" \
		python -m ${openfisca} test \
		$(call tests,"openfisca_country_template") \
		--country-package openfisca_country_template \
		${openfisca_args}
	@$(call print_pass,$@:)

## Run extension-template tests.
test-extension:
	@$(call print_help,$@:)
	@PYTEST_ADDOPTS="$${PYTEST_ADDOPTS} ${pytest_args}" \
		python -m ${openfisca} test \
		$(call tests,"openfisca_extension_template") \
		--country-package openfisca_country_template \
		--extensions openfisca_extension_template \
		${openfisca_args}
	@$(call print_pass,$@:)

## Print the coverage report.
test-cov:
	@$(call print_help,$@:)
	@python -m coverage report
	@$(call print_pass,$@:)
