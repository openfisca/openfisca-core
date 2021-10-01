## Lint the codebase.
lint: check-syntax-errors check-style check-types
	@$(call print_pass,$@:)

## Compile python files to check for syntax errors.
check-syntax-errors: .
	@$(call print_help,$@:)
	@python -m compileall -q $?
	@$(call print_pass,$@:)

## Run linters to check for syntax and style errors.
check-style: $(shell git ls-files "*.py")
	@$(call print_help,$@:)
	@flake8 $?
	@$(call print_pass,$@:)

## Run static type checkers for type errors.
check-types: openfisca_core openfisca_web_api
	@$(call print_help,$@:)
	@mypy $?
	@$(call print_pass,$@:)

## Run code formatters to correct style errors.
format-style: $(shell git ls-files "*.py")
	@$(call print_help,$@:)
	@autopep8 $?
	@$(call print_pass,$@:)
