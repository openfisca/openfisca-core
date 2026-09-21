## Lint the codebase.
lint: check-syntax-errors check-style
	@$(call print_pass,$@:)

## Compile python files to check for syntax errors.
check-syntax-errors: .
	@$(call print_help,$@:)
	@python -m compileall -q $?
	@$(call print_pass,$@:)

## Run linters to check for syntax and style errors.
check-style:
	@$(call print_help,$@:)
	@ruff check
	@codespell
	@$(call print_pass,$@:)

## Run static type checkers for type errors.
check-types:
	@$(call print_help,$@:)
	@python -m mypy \
		openfisca_core/commons \
		openfisca_core/data_storage \
		openfisca_core/experimental \
		openfisca_core/entities \
		openfisca_core/indexed_enums \
		openfisca_core/periods \
		openfisca_core/types.py
	@$(call print_pass,$@:)

## Run code formatters to correct style errors.
format-style:
	@$(call print_help,$@:)
	@ruff format --fix
	@codespell --write-changes
	@$(call print_pass,$@:)
