## The repository of the documentation.
repo = https://github.com/openfisca/openfisca-doc

## The current working branch.
branch = $(shell git branch --show-current)

## Check that the current changes do not break the doc.
test-doc:
	@##	Usage:
	@##
	@##		make test-doc [branch=BRANCH]
	@##
	@##	Examples:
	@##
	@##		# Will check the current branch in openfisca-doc.
	@##		make test-doc
	@##
	@##		# Will check "test-doc" in openfisca-doc.
	@##		make test-doc branch=test-doc
	@##
	@##		# Will check "master" if "asdf1234" does not exist.
	@##		make test-doc branch=asdf1234
	@##
	@$(call print_help,$@:)
	@${MAKE} test-doc-checkout
	@${MAKE} test-doc-install
	@${MAKE} test-doc-build
	@$(call print_pass,$@:)

## Update the local copy of the doc.
test-doc-checkout:
	@$(call print_help,$@:)
	@[ ! -d doc ] && git clone ${repo} doc || :
	@cd doc && { \
		git reset --hard ; \
		git fetch --all ; \
		[ "$$(git branch --show-current)" != "master" ] && git checkout master || : ; \
		[ "${branch}" != "master" ] \
			&& { \
				{ \
					>&2 echo "$(print_info) Trying to checkout the branch 'openfisca-doc/${branch}'..." ; \
					git branch -D ${branch} 2> /dev/null ; \
					git checkout ${branch} 2> /dev/null ; \
				} \
					&& git pull --ff-only origin ${branch} \
					|| { \
						>&2 echo "$(print_warn) The branch 'openfisca-doc/${branch}' was not found, falling back to 'openfisca-doc/master'..." ; \
						>&2 echo "" ; \
						>&2 echo "$(print_info) This is perfectly normal, one of two things can ensue:" ; \
						>&2 echo "$(print_info)" ; \
						>&2 echo "$(print_info) $$(tput setaf 2)[If tests pass]$$(tput sgr0)" ; \
						>&2 echo "$(print_info)     * No further action required on your side..." ; \
						>&2 echo "$(print_info)" ; \
						>&2 echo "$(print_info) $$(tput setaf 1)[If tests fail]$$(tput sgr0)" ; \
						>&2 echo "$(print_info)     * Create the branch '${branch}' in 'openfisca-doc'... " ; \
						>&2 echo "$(print_info)     * Push your fixes..." ; \
						>&2 echo "$(print_info)     * Run 'make test-doc' again..." ; \
						>&2 echo "" ; \
						>&2 echo "$(print_work) Checking out 'openfisca-doc/master'..." ; \
						git pull --ff-only origin master ; \
					} \
			} \
			|| git pull --ff-only origin master ; \
	} 1> /dev/null
	@$(call print_pass,$@:)

## Install doc dependencies.
test-doc-install:
	@$(call print_help,$@:)
	@pip install --requirement doc/requirements.txt 1> /dev/null
	@pip install --editable .[dev] --upgrade 1> /dev/null
	@$(call print_pass,$@:)

## Dry-build the doc.
test-doc-build:
	@$(call print_help,$@:)
	@sphinx-build -M dummy doc/source doc/build -n -q -W
	@$(call print_pass,$@:)
