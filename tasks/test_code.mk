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
test-core: $(shell git ls-files "tests/*.py")
	@$(call print_help,$@:)
	@PYTEST_ADDOPTS="${PYTEST_ADDOPTS} --cov=openfisca_core ${pytest_args}" \
		openfisca test $? \
		${openfisca_args}
	@$(call print_pass,$@:)
