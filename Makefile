doc = sed -n "/^$1/ { x ; p ; } ; s/\#\#/[⚙]/ ; s/\./.../ ; x" ${MAKEFILE_LIST}

## Same as `make test.
all: test

## Install project dependencies.
install:
	@echo [⚙] Installing dependencies...
	@pip install --upgrade pip twine wheel
	@pip install --editable .[dev] --upgrade --use-deprecated=legacy-resolver

## Install openfisca-core for deployment and publishing.
build: setup.py
	@## This allows us to be sure tests are run against the packaged version
	@## of openfisca-core, the same we put in the hands of users and reusers.
	@echo [⚙] Building and installing locally built openfisca-core...
	@python $? bdist_wheel
	@find dist -name "*.whl" -exec pip install --force-reinstall {}[dev] \;

## Uninstall project dependencies.
uninstall:
	@echo [⚙] Uninstalling project dependencies...
	@pip freeze | grep -v "^-e" | sed "s/@.*//" | xargs pip uninstall -y

## Delete builds and compiled python files.
clean: \
	$(shell ls -d * | grep "build\|dist") \
	$(shell find . -name "*.pyc")
	@echo [⚙] Deleting builds and compiled python files...
	@rm -rf $?

## Compile python files to check for syntax errors.
check-syntax-errors: .
	@echo [⚙] Compiling python files to check for syntax errors...
	@python -m compileall -q $?

## Run linters to check for syntax and style errors.
check-style: $(shell git ls-files "*.py")
	@echo [⚙] Running linters to check for syntax and style errors...
	@flake8 $?

## Run code formatters to correct style errors.
format-style: $(shell git ls-files "*.py")
	@echo [⚙] Running code formatters to correct style errors...
	@autopep8 $?

## Run static type checkers for type errors.
check-types: openfisca_core openfisca_web_api
	@echo [⚙] Running static type checkers for type errors...
	@mypy $?

## Run openfisca-core tests.
test: clean check-syntax-errors check-style check-types
	@echo [⚙] Running openfisca-core tests...
	@env PYTEST_ADDOPTS="${PYTEST_ADDOPTS} --cov=openfisca_core" pytest

## Serve the openfisca Web API.
api:
	@echo [⚙] Serving the openfisca Web API...
	@openfisca serve \
		--country-package openfisca_country_template \
		--extensions openfisca_extension_template
