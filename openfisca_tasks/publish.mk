.PHONY: build

## Build openfisca-core for deployment and publishing.
build:
	@## This allows us to be sure tests are run against the packaged version
	@## of openfisca-core, the same we put in the hands of users and reusers.
	@$(call print_help,$@:)
	@${MAKE} install-deps
	@${MAKE} build-deps
	@${MAKE} build-build
	@${MAKE} build-install
	@$(call print_pass,$@:)

## Install building dependencies.
build-deps:
	@$(call print_help,$@:)
	@pip install --quiet --upgrade --constraint requirements/publication build

## Build the package.
build-build:
	@$(call print_help,$@:)
	@python -m build

## Install the built package.
build-install:
	@$(call print_help,$@:)
	@pip uninstall --quiet --yes openfisca-core
	@find dist -name "*.whl" -exec pip install --quiet --no-dependencies {} \;

## Publish package.
publish:
	@$(call print_help,$@:)
	@${MAKE} publish-deps
	@${MAKE} publish-upload
	@$(call print_pass,$@:)

## Install required publishing dependencies.
publish-deps:
	@$(call print_help,$@:)
	@pip install --quiet --upgrade --constraint requirements/publication twine

## Upload package to PyPi.
publish-upload:
	@$(call print_help,$@:)
	twine upload dist/* --username $${PYPI_USERNAME} --password $${PYPI_PASSWORD}
