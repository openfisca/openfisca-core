## The openfisca command module.
openfisca = openfisca_core.scripts.openfisca_command

## The path to the country template tests.
country = $(shell python -c "import pathlib, $(1); print(pathlib.Path($(1).__path__[0]) / 'tests')")

## The path to the extension template tests.
extension = $(shell python -c "import pathlib, $(1); print(pathlib.Path($(1).__path__[0]) / '..' / 'tests' / '$(1)')")

## Run all tasks required for testing.
install: install-deps install-edit install-test

## Enable regression testing with template repositories.
install-test:
	@$(call print_help,$@:)
	@python -m pip install --no-deps --upgrade --no-binary :all: \
		openfisca-country-template openfisca-extension-template

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
	@PYTEST_ADDOPTS="$${PYTEST_ADDOPTS} ${pytest_args}" \
		python -m ${openfisca} test \
		openfisca_core/commons \
		openfisca_core/data_storage \
		openfisca_core/experimental \
		openfisca_core/entities \
		openfisca_core/holders \
		openfisca_core/indexed_enums \
		openfisca_core/periods \
		openfisca_core/projectors \
		${openfisca_args}
		python -m pytest tests/
	@$(call print_pass,$@:)

## Run country-template tests.
test-country:
	@$(call print_help,$@:)
	@PYTEST_ADDOPTS="$${PYTEST_ADDOPTS} ${pytest_args}" \
		python -m ${openfisca} test \
		$(call country,"openfisca_country_template") \
		--country-package openfisca_country_template \
		${openfisca_args}
	@$(call print_pass,$@:)

## Run extension-template tests.
test-extension:
	@$(call print_help,$@:)
	@PYTEST_ADDOPTS="$${PYTEST_ADDOPTS} ${pytest_args}" \
		python -m ${openfisca} test \
		$(call extension,"openfisca_extension_template") \
		--country-package openfisca_country_template \
		--extensions openfisca_extension_template \
		${openfisca_args}
	@$(call print_pass,$@:)
