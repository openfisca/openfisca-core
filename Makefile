include tasks/install.mk
include tasks/lint.mk
include tasks/publish.mk
include tasks/serve.mk
include tasks/test_code.mk

## To share info with the user, but no action is needed.
print_info = $$(tput setaf 6)[i]$$(tput sgr0)

## To warn the user of something, but no action is needed.
print_warn = $$(tput setaf 3)[!]$$(tput sgr0)

## To let the user know where we are in the task pipeline.
print_work = $$(tput setaf 5)[⚙]$$(tput sgr0)

## To let the user know the task in progress succeeded.
## The `$1` is a function argument, passed from a task (usually the task name).
print_pass = echo $$(tput setaf 2)[✓]$$(tput sgr0) $$(tput setaf 8)$1$$(tput sgr0)$$(tput setaf 2)passed$$(tput sgr0) $$(tput setaf 1)❤$$(tput sgr0)

## Similar to `print_work`, but this will read the comments above a task, and
## print them to the user at the start of each task. The `$1` is a function
## argument.
print_help = sed -n "/^$1/ { x ; p ; } ; s/\#\#/\r$(print_work)/ ; s/\./…/ ; x" ${MAKEFILE_LIST}

## Same as `make`.
.DEFAULT_GOAL := all

## Same as `make test`.
all: test
	@$(call print_pass,$@:)

## Run all lints and tests.
test: clean lint test-code
	@$(call print_pass,$@:)
