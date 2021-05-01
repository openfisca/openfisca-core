## Install project dependencies.
install:
	@$(call print_help,$@:)
	@pip install --upgrade pip setuptools
	@pip install --requirement requirements/dev --upgrade
	@pip install --editable . --upgrade --no-dependencies

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
