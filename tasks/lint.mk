## Lint the codebase.
lint: check-syntax-errors check-style check-types
	@$(call print_pass,$@:)

## Compile python files to check for syntax errors.
check-syntax-errors: .
	@$(call print_help,$@:)
	@python -m compileall -q $?
	@$(call print_pass,$@:)

## Run linters to check for syntax and style errors.
check-style:
	@$(call print_help,$@:)
	@flake8 $(shell git ls-files "*.py")
	@$(call print_pass,$@:)

## Run static type checkers for type errors.
check-types:
	@$(call print_help,$@:)
	@mypy src
	@$(call print_pass,$@:)

## Run code formatters to correct style errors.
format-style:
	@$(call print_help,$@:)
	@autopep8 $(shell find . -name "*.py")
	@$(call print_pass,$@:)
