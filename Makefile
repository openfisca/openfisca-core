help = sed -n "/^$1/ { x ; p ; } ; s/\#\#/[⚙]/ ; s/\./.../ ; x" ${MAKEFILE_LIST}
repo = https://github.com/openfisca/openfisca-doc
branch = $(shell git branch --show-current)

## Same as `make test`.
all: test

## Install project dependencies.
install:
	@$(call help,$@:)
	@pip install --upgrade pip twine wheel
	@pip install --editable .[dev] --upgrade --use-deprecated=legacy-resolver

## Install openfisca-core for deployment and publishing.
build: setup.py
	@## This allows us to be sure tests are run against the packaged version
	@## of openfisca-core, the same we put in the hands of users and reusers.
	@$(call help,$@:)
	@python $? bdist_wheel
	@find dist -name "*.whl" -exec pip install --force-reinstall {}[dev] \;

## Uninstall project dependencies.
uninstall:
	@$(call help,$@:)
	@pip freeze | grep -v "^-e" | sed "s/@.*//" | xargs pip uninstall -y

## Delete builds, cached and compiled python files.
clean: \
	$(shell ls -a | grep "build\|dist\|mypy_\|pytest_") \
	$(shell find . -path ./.nox -prune -o -name "*.pyc")
	@$(call help,$@:)
	@rm -rf $?

## Compile python files to check for syntax errors.
check-syntax-errors: .
	@$(call help,$@:)
	@python -m compileall -q $?

## Run linters to check for syntax and style errors.
check-style: $(shell git ls-files "*.py")
	@$(call help,$@:)
	@flake8 $?

## Run code formatters to correct style errors.
format-style: $(shell git ls-files "*.py")
	@$(call help,$@:)
	@autopep8 $?

## Run static type checkers for type errors.
check-types: openfisca_core openfisca_web_api
	@$(call help,$@:)
	@mypy $?

## Run openfisca-core tests.
test: clean check-syntax-errors check-style check-types
	@$(call help,$@:)
	@env PYTEST_ADDOPTS="${PYTEST_ADDOPTS} --cov=openfisca_core" pytest

## Run openfisca-core tests over a matrix.
test.matrix:
	@$(call doc,$@:)
	@[ -z $$(pip freeze | grep ^nox) ] \
		&& pip install --upgrade nox \
		&& ${MAKE} test.matrix \
		|| time ${MAKE} test.matrix.all --jobs $$(($$(nproc) / 2 + 1))

test.matrix.%: $(shell git ls-files "tests/**/*.py")
	@args=($(subst -, ,$*)) ; nox -s "test-$${args[0]}($${args[1]})" -- $?

test.matrix.all: \
	test.matrix.3.7.11-1.18.5 \
	test.matrix.3.7.11-1.19.5 \
	test.matrix.3.7.11-1.20.3 \
	test.matrix.3.7.11-1.21.2 \
	test.matrix.3.8.12-1.18.5 \
	test.matrix.3.8.12-1.19.5 \
	test.matrix.3.8.12-1.20.3 \
	test.matrix.3.8.12-1.21.2 \
	test.matrix.3.9.7-1.18.5 \
	test.matrix.3.9.7-1.19.5 \
	test.matrix.3.9.7-1.20.3 \
	test.matrix.3.9.7-1.21.2 \
	;

## Check that the current changes do not break the doc.
test-doc:
	@##	Usage:
	@##
	@##		make test-doc [branch=BRANCH]
	@##
	@##	Examples:
	@##
	@##		# Will check the current branch in openfisca-doc.
	@##		make test-doc
	@##
	@##		# Will check "test-doc" in openfisca-doc.
	@##		make test-doc branch=test-doc
	@##
	@##		# Will check "master" if "asdf1234" does not exist.
	@##		make test-doc branch=asdf1234
	@##
	@$(call help,$@:)
	@${MAKE} test-doc-checkout
	@${MAKE} test-doc-install
	@${MAKE} test-doc-build

## Update the local copy of the doc.
test-doc-checkout:
	@$(call help,$@:)
	@[ ! -d doc ] && git clone ${repo} doc || :
	@cd doc && { \
		git reset --hard ; \
		git fetch --all ; \
		[ $$(git branch --show-current) != master ] && git checkout master || : ; \
		[ ${branch} != "master" ] \
			&& { \
				{ \
					git branch -D ${branch} 2> /dev/null ; \
					git checkout ${branch} ; \
				} \
					&& git pull --ff-only origin ${branch} \
					|| { \
						>&2 echo "[!] The branch '${branch}' doesn't exist, checking out 'master' instead..." ; \
						git pull --ff-only origin master ; \
					} \
			} \
			|| git pull --ff-only origin master ; \
	} 1> /dev/null

## Install doc dependencies.
test-doc-install:
	@$(call help,$@:)
	@pip install --requirement doc/requirements.txt 1> /dev/null
	@pip install --editable .[dev] --upgrade 1> /dev/null

## Dry-build the doc.
test-doc-build:
	@$(call help,$@:)
	@sphinx-build -M dummy doc/source doc/build -n -q -W

## Serve the openfisca Web API.
api:
	@$(call help,$@:)
	@openfisca serve \
		--country-package openfisca_country_template \
		--extensions openfisca_extension_template
