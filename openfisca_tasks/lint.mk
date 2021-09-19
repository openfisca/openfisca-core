## Lint the codebase.
lint: check-syntax-errors check-style lint-styling-doc check-types
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

## Run linters to check for syntax and style errors in the doc.
lint-styling-doc: \
	lint-styling-doc-commons \
	lint-styling-doc-types \
	;

## Run linters to check for syntax and style errors in the doc.
lint-styling-doc-%:
	@## These checks are exclusively related to doc/strings/test.
	@##
	@## They can be integrated into setup.cfg once all checks pass.
	@## The reason they're here is because otherwise we wouldn't be
	@## able to integrate documentation improvements progresively.
	@##
	@## D101:	Each class has to have at least one doctest.
	@## D102:	Each public method has to have at least one doctest.
	@## D103:	Each public function has to have at least one doctest.
	@## DARXXX:	https://github.com/terrencepreilly/darglint#error-codes.
	@##
	@$(call print_help,$(subst $*,%,$@:))
	@flake8 --select=D101,D102,D103,DAR openfisca_core/$*
	@pylint openfisca_core/$*
	@$(call print_pass,$@:)

## Run static type checkers for type errors.
check-types:
	@$(call print_help,$@:)
	@mypy --package openfisca_core --package openfisca_web_api
	@$(call print_pass,$@:)

## Run code formatters to correct style errors.
format-style: $(shell git ls-files "*.py")
	@$(call print_help,$@:)
	@autopep8 $?
	@$(call print_pass,$@:)
