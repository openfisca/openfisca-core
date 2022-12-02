.PHONY: build

## Install project's build dependencies.
install-dist:
	@$(call print_help,$@:)
	@python setup.py egg_info
	@python -m pip install $$(grep -v "^\[" *.egg-info/requires.txt)
	@$(call print_pass,$@:)

## Build & install openfisca-core for deployment and publishing.
build:
	@## This allows us to be sure tests are run against the packaged version
	@## of openfisca-core, the same we put in the hands of users and reusers.
	@$(call print_help,$@:)
	@python -m build
	@pip uninstall --yes openfisca-core
	@find dist -name "*.whl" -exec python -m pip install --no-deps {} \;
	@$(call print_pass,$@:)

## Upload to PyPi.
publish:
	@$(call print_help,$@:)
	@python -m twine upload dist/* \
		--username $PYPI_USERNAME \
		--password $PYPI_PASSWORD
	@$(call print_pass,$@:)
