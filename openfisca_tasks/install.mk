## Install project dependencies.
install:
	@$(call print_help,$@:)
	@pip install --upgrade pip twine wheel
	@pip install --editable ".[dev,test]" --upgrade

## Uninstall project dependencies.
uninstall:
	@$(call print_help,$@:)
	@pip freeze | grep -v "^-e" | sed "s/@.*//" | xargs pip uninstall -y

## Delete builds and compiled python files.
clean: \
	$(shell ls -d * | grep "build\|dist") \
	$(shell find . -name "*.pyc")
	@$(call print_help,$@:)
	@rm -rf $?
