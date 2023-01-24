## Lint the codebase.
lint: compile lint-doc lint-style lint-typing lint-typing-strict
	@$(call print_pass,$@:)

## Compile python files to check for syntax errors.
compile: .
	@$(call print_help,$@:)
	@python -m compileall -q $?
	@$(call print_pass,$@:)

## Run linters to check for syntax and style errors.
lint-style: $(shell git ls-files "*.py")
	@$(call print_help,$@:)
	@python -m flake8 $?
	@$(call print_pass,$@:)

## Run linters to check for syntax and style errors in the doc.
lint-doc: \
	lint-doc-commons \
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
	@python -m flake8 --select=D101,D102,D103,DAR openfisca_core/$*
	@python -m pylint openfisca_core/$*
	@$(call print_pass,$@:)

## Run static type checkers for type errors.
lint-typing:
	@$(call print_help,$@:)
	@python -m mypy --package openfisca_core --package openfisca_web_api
	@$(call print_pass,$@:)

## Run static type checkers for type errors (strict).
lint-typing-strict: \
	lint-typing-strict-commons \
	lint-typing-strict-types \
	;

## Run static type checkers for type errors (strict).
lint-typing-strict-%:
	@$(call print_help,$(subst $*,%,$@:))
	@python -m mypy \
		--cache-dir .mypy_cache-openfisca_core.$* \
		--implicit-reexport \
		--strict \
		--package openfisca_core.$*
	@$(call print_pass,$@:)

## Run code formatters to correct style errors.
format-style: $(shell git ls-files "*.py")
	@$(call print_help,$@:)
	@python -m autopep8 $?
	@$(call print_pass,$@:)
