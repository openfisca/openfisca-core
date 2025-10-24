## Uninstall project's dependencies.
uninstall:
	@$(call print_help,$@:)
	@python -m pip freeze | grep -v "^-e" | sed "s/@.*//" | xargs pip uninstall -y

## Install project's overall dependencies
install-deps:
	@$(call print_help,$@:)
	@python -m pip install --upgrade pip

## Install project's development dependencies.
install-edit:
	@$(call print_help,$@:)
	@python -m pip install --upgrade --editable ".[dev]"

## Delete builds and compiled python files.
clean:
	@$(call print_help,$@:)
	@ls -d * | grep "build\|dist" | xargs rm -rf
	@find . -name "__pycache__" | xargs rm -rf
	@find . -name "*.pyc" | xargs rm -rf
