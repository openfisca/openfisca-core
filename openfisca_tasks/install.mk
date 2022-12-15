## Uninstall project's dependencies.
uninstall:
	@$(call print_help,$@:)
	@pip freeze | grep -v "^-e" | sed "s/@.*//" | xargs pip uninstall -y

## Install project's overall dependencies
install-deps:
	@$(call print_help,$@:)
	@pip install --upgrade pip twine wheel

## Install project's development dependencies.
install-edit:
	@$(call print_help,$@:)
	@pip install --upgrade --editable ".[dev]"

## Delete builds and compiled python files.
clean:
	@$(call print_help,$@:)
	@ls -d * | grep "build\|dist" | xargs rm -rf
	@find . -name "*.pyc" | xargs rm -rf
