## Install building utils.
install-builder:
	@$(call print_help,$@:)
	@pip install --upgrade pip setuptools wheel

## Install publishing tools.
install-publisher:
	@$(call print_help,$@:)
	@pip install --upgrade twine

## Install build dependencies.
install-deps:
	@## Create a requirements file & install openfisca's dependencies.
	@$(call print_help,$@:)
	python setup.py egg_info
	pip install $(shell grep -v "^\[" *.egg-info/requires.txt)
	@$(call print_pass,$@:)

## Build & install openfisca-core for deployment and publishing.
build:
	@## This allows us to be sure tests are run against the packaged version
	@## of openfisca-core, the same we put in the hands of users and reusers.
	@$(call print_help,$@:)
	@python setup.py bdist_wheel
	@find dist -name "*.whl" -exec pip install --force-reinstall --no-dependencies {} \;
	@$(call print_pass,$@:)

## Upload openfisca-core package to PyPi.
publish:
	@twine upload dist/* --username $${PYPI_USERNAME} --password $${PYPI_PASSWORD}
