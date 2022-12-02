## The openfisca command module.
openfisca = openfisca_core.scripts.openfisca_command

## The path to the installed packages.
python_packages = $(shell python -c "import sysconfig; print(sysconfig.get_paths()[\"purelib\"])")

## Run all tasks required for testing.
install: install-deps install-edit install-test

## Enable regression testing with template repositories.
install-test:
	@$(call print_help,$@:)
	python -m pip install --upgrade --no-deps openfisca-country-template
	python -m pip install --upgrade --no-deps openfisca-extension-template
	@$(call print_pass,$@:)

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
test-core: $(shell python -m pytest --quiet --quiet --collect-only 2> /dev/null | cut -f 1 -d ":")
	@$(call print_help,$@:)
	@python -m pytest --quiet --capture=no --xdoctest --xdoctest-verbose=0 \
		openfisca_core/commons \
		openfisca_core/holders \
		openfisca_core/types
	@PYTEST_ADDOPTS="$${PYTEST_ADDOPTS} ${pytest_args}" \
		python -m coverage run -m \
		${openfisca} test $? \
		${openfisca_args}
	@$(call print_pass,$@:)

## Run country-template tests.
test-country:
	@$(call print_help,$@:)
	@PYTEST_ADDOPTS="$${PYTEST_ADDOPTS} ${pytest_args}" \
		python -m ${openfisca} test \
		${python_packages}/openfisca_country_template/tests \
		--country-package openfisca_country_template \
		${openfisca_args}
	@$(call print_pass,$@:)

## Run extension-template tests.
test-extension:
	@$(call print_help,$@:)
	@PYTEST_ADDOPTS="$${PYTEST_ADDOPTS} ${pytest_args}" \
		python -m ${openfisca} test \
		${python_packages}/openfisca_extension_template/tests \
		--country-package openfisca_country_template \
		--extensions openfisca_extension_template \
		${openfisca_args}
	@$(call print_pass,$@:)

## Print the coverage report.
test-cov:
	@$(call print_help,$@:)
	@python -m coverage report
	@$(call print_pass,$@:)
