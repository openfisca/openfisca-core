## Lint the codebase.
lint: check-syntax-errors check-style lint-doc
	@$(call print_pass,$@:)

## Compile python files to check for syntax errors.
check-syntax-errors: .
	@$(call print_help,$@:)
	@python -m compileall -q $?
	@$(call print_pass,$@:)

## Run linters to check for syntax and style errors.
check-style: $(shell git ls-files "*.py")
	@$(call print_help,$@:)
	@isort --check $?
	@black --check $?
	@flake8 $?
	@$(call print_pass,$@:)

## Run linters to check for syntax and style errors in the doc.
lint-doc: \
	lint-doc-commons \
	lint-doc-entities \
	lint-doc-types \
	;

## Run linters to check for syntax and style errors in the doc.
lint-doc-%:
	@## These checks are exclusively related to doc/strings/test.
	@##
	@## They can be integrated into setup.cfg once all checks pass.
	@## The reason they're here is because otherwise we wouldn't be
	@## able to integrate documentation improvements progresively.
	@##
	@$(call print_help,$(subst $*,%,$@:))
	@flake8 --select=D101,D102,D103,DAR openfisca_core/$*
	@pylint openfisca_core/$*
	@$(call print_pass,$@:)

## Run static type checkers for type errors.
check-types:
	@$(call print_help,$@:)
	@mypy \
		openfisca_core/commons \
		openfisca_core/types.py
	@$(call print_pass,$@:)

## Run code formatters to correct style errors.
format-style: $(shell git ls-files "*.py")
	@$(call print_help,$@:)
	@isort $?
	@black $?
	@$(call print_pass,$@:)
