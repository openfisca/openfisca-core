## The path to the installed packages.
python_packages = $(shell python -c "import sysconfig; print(sysconfig.get_paths()[\"purelib\"])")

## Run openfisca-core.
test-code: test-core
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
	@$(call print_pass,$@:)

## Run openfisca-core tests.
test-core:
	@$(call print_help,$@:)
	@PYTEST_ADDOPTS="\
		${PYTEST_ADDOPTS} \
		--cov=src \
		${pytest_args} \
		" \
		openfisca test $(shell find tests -name "*.py") ${openfisca_args}
	@$(call print_pass,$@:)

## Run openfisca-core tests against the built version.
test-built:
	@$(call print_help,$@:)
	@PYTEST_ADDOPTS=" \
		${PYTEST_ADDOPTS} \
		--cov=${python_packages}/openfisca_core \
		--cov=${python_packages}/openfisca_web_api \
		${pytest_args} \
		" \
		openfisca test $(shell find tests -name "*.py") ${openfisca_args}
	@$(call print_pass,$@:)
