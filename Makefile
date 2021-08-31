doc = sed -n "/^$1/ { x ; p ; } ; s/\#\#/[⚙]/ ; s/\./.../ ; x" ${MAKEFILE_LIST}

## Same as `make test.
all: test

## Install project dependencies.
install:
	@$(call doc,$@:)
	@pip install --upgrade pip twine wheel
	@pip install --editable .[dev] --upgrade --use-deprecated=legacy-resolver

## Install openfisca-core for deployment and publishing.
build: setup.py
	@## This allows us to be sure tests are run against the packaged version
	@## of openfisca-core, the same we put in the hands of users and reusers.
	@$(call doc,$@:)
	@python $? bdist_wheel
	@find dist -name "*.whl" -exec pip install --force-reinstall {}[dev] \;

## Uninstall project dependencies.
uninstall:
	@$(call doc,$@:)
	@pip freeze | grep -v "^-e" | sed "s/@.*//" | xargs pip uninstall -y

## Delete builds and compiled python files.
clean: \
	$(shell ls -d * | grep "build\|dist") \
	$(shell find . -name "*.pyc")
	@$(call doc,$@:)
	@rm -rf $?

## Compile python files to check for syntax errors.
check-syntax-errors: .
	@$(call doc,$@:)
	@python -m compileall -q $?

## Run linters to check for syntax and style errors.
check-style: $(shell git ls-files "*.py")
	@$(call doc,$@:)
	@flake8 $?

## Run code formatters to correct style errors.
format-style: $(shell git ls-files "*.py")
	@$(call doc,$@:)
	@autopep8 $?

## Run static type checkers for type errors.
check-types: openfisca_core openfisca_web_api
	@$(call doc,$@:)
	@mypy $?

## Run openfisca-core tests.
test: clean check-syntax-errors check-style check-types
	@$(call doc,$@:)
	@env PYTEST_ADDOPTS="${PYTEST_ADDOPTS} --cov=openfisca_core" pytest

## Serve the openfisca Web API.
api:
	@$(call doc,$@:)
	@openfisca serve \
		--country-package openfisca_country_template \
		--extensions openfisca_extension_template
