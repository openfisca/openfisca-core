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
	@$(call print_help,$@:)
	@python setup.py egg_info
	@pip install $$(grep -v "^\[" *.egg-info/requires.txt)
	@$(call print_pass,$@:)

## Build & install openfisca-core for deployment and publishing.
build:
	@$(call print_help,$@:)
	@python setup.py bdist_wheel
	@find dist -name "*.whl" -exec pip install --force-reinstall --no-dependencies {} \;
	@$(call print_pass,$@:)

## Upload openfisca-core package to PyPi.
publish:
	@twine upload dist/* --username $${PYPI_USERNAME} --password $${PYPI_PASSWORD}
