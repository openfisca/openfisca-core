## Install project dependencies.
install:
	@${MAKE} install-deps
	@${MAKE} install-dev
	@${MAKE} install-core
	@$(call print_pass,$@:)

## Install common dependencies.
install-deps:
	@$(call print_help,$@:)
	@pip install --quiet --upgrade --constraint requirements/common pip setuptools

## Install development dependencies.
install-dev:
	@$(call print_help,$@:)
	@pip install --quiet --upgrade --requirement requirements/install
	@pip install --quiet --upgrade --requirement requirements/dev

## Install package.
install-core:
	@$(call print_help,$@:)
	@pip uninstall --quiet --yes openfisca-core
	@pip install --quiet --no-dependencies --editable .

## Install the WebAPI tracker.
install-tracker:
	@$(call print_help,$@:)
	@pip install --quiet --upgrade --constraint requirements/tracker openfisca-tracker

## Install lower-bound dependencies for compatibility check.
install-compat:
	@$(call print_help,$@:)
	@pip install --quiet --upgrade --constraint requirements/compatibility numpy

## Install coverage dependencies.
install-cov:
	@$(call print_help,$@:)
	@pip install --quiet --upgrade --constraint requirements/coverage coveralls

## Uninstall project dependencies.
uninstall:
	@$(call print_help,$@:)
	@pip freeze | grep -v "^-e" | sed "s/@.*//" | xargs pip uninstall -y

## Delete builds and compiled python files.
clean: \
	$(shell ls -d * | grep "build\|dist") \
	$(shell find . -name "*.pyc")
	@$(call print_help,$@:)
	@rm -rf $?
