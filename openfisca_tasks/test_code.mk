## The path to the installed packages.
python_packages = $(shell python -c "import sysconfig; print(sysconfig.get_paths()[\"purelib\"])")

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
test-core: $(shell git ls-files "tests/*.py")
	@$(call print_help,$@:)
	@PYTEST_ADDOPTS="${PYTEST_ADDOPTS} --cov=openfisca_core ${pytest_args}" \
		openfisca test $? \
		${openfisca_args}
	@$(call print_pass,$@:)

## Run country-template tests.
test-country:
	@$(call print_help,$@:)
	@PYTEST_ADDOPTS="${PYTEST_ADDOPTS} ${pytest_args}" \
		openfisca test ${python_packages}/openfisca_country_template/tests \
		--country-package openfisca_country_template \
		${openfisca_args}
	@$(call print_pass,$@:)

## Run extension-template tests.
test-extension:
	@$(call print_help,$@:)
	@PYTEST_ADDOPTS="${PYTEST_ADDOPTS} ${pytest_args}" \
		openfisca test ${python_packages}/openfisca_extension_template/tests \
		--country-package openfisca_country_template \
		--extensions openfisca_extension_template \
		${openfisca_args}
	@$(call print_pass,$@:)
