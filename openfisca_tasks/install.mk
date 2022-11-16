## Install overall dependencies
install-deps:
	@$(call print_help,$@:)
	@python -m pip install --upgrade pip twine wheel
	@python -m pip install --upgrade --no-dependencies openfisca-country-template
	@python -m pip install --upgrade --no-dependencies openfisca-extension-template

## Install project dependencies.
install: install-deps
	@$(call print_help,$@:)
	@python -m pip install --upgrade --editable ".[dev]"

## Uninstall project dependencies.
uninstall:
	@$(call print_help,$@:)
	@python -m pip freeze | grep -v "^-e" | sed "s/@.*//" | xargs python -m pip uninstall -y

## Delete builds and compiled python files.
clean:
	@$(call print_help,$@:)
	@ls -d * | grep "build\|dist" | xargs rm -rf
	@find . -name "*.pyc" | xargs rm -rf
