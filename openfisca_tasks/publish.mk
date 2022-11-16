.PHONY: build

## Install openfisca-core for deployment and publishing.
build: install-deps
	@## This allows us to be sure tests are run against the packaged version
	@## of openfisca-core, the same we put in the hands of users and reusers.
	@$(call print_help,$@:)
	@python -m pip install --upgrade build
	@python -m build
	@python -m pip uninstall --yes openfisca-core
	@find dist -name "*.whl" -exec python -m pip install {}[dev] \;
	@$(call print_pass,$@:)
