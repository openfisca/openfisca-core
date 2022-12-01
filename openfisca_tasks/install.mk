## Uninstall project's dependencies.
uninstall:
	@$(call print_help,$@:)
	@python -m pip freeze | grep -v "^-e" | sed "s/@.*//" | xargs python -m pip uninstall -y
	@$(call print_pass,$@:)

## Install project's overall dependencies
install-deps:
	@$(call print_help,$@:)
	@python -m pip install --upgrade pip
	@$(call print_pass,$@:)

## Install project's development dependencies.
install-edit:
	@$(call print_help,$@:)
	@python -m pip install --upgrade --editable ".[dev]"
	@$(call print_pass,$@:)

## Delete builds and compiled python files.
clean:
	@$(call print_help,$@:)
	@ls -d * | grep "build\|dist" | xargs rm -rf
	@find . -name "__pycache__" | xargs rm -rf
	@find . -name "*.pyc" | xargs rm -rf
	@$(call print_pass,$@:)
