include openfisca_tasks/install.mk
include openfisca_tasks/lint.mk
include openfisca_tasks/publish.mk
include openfisca_tasks/serve.mk
include openfisca_tasks/test_code.mk
include openfisca_tasks/test_doc.mk

print_help = sed -n "/^$1/ { x ; p ; } ; s/\#\#/[⚙]/ ; s/\./.../ ; x" ${MAKEFILE_LIST}

.DEFAULT_GOAL := all

## Same as `make test`.
all: test

## Run all lints and tests.
test: clean lint test-code
