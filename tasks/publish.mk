.PHONY: build

## Install project's build dependencies.
install-dist:
	@$(call print_help,$@:)
	@python -m pip install .[ci,dev] build
	@$(call print_pass,$@:)

## Build & install openfisca-core for deployment and publishing.
build:
	@## This allows us to be sure tests are run against the packaged version
	@## of openfisca-core, the same we put in the hands of users and reusers.
	@$(call print_help,$@:)
	@python -m pip install --upgrade pip
	@python -m pip install build
	@python -m pip list | grep build
	@python -m build
	@python -m pip uninstall --yes openfisca-core
	@find dist -name "*.whl" -exec python -m pip install --no-deps {} \;
	@$(call print_pass,$@:)
