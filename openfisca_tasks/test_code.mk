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

## Run openfisca-core tests.
test-core: $(shell git ls-files "tests/*.py")
	@$(call help,$@:)
	@PYTEST_ADDOPTS="${PYTEST_ADDOPTS} --cov=openfisca_core ${pytest_args}" \
		openfisca test $? \
		${openfisca_args}
