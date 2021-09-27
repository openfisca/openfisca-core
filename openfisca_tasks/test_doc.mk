repo = https://github.com/openfisca/openfisca-doc
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
	@$(call help,$@:)
	@${MAKE} test-doc-checkout
	@${MAKE} test-doc-install
	@${MAKE} test-doc-build

## Update the local copy of the doc.
test-doc-checkout:
	@$(call help,$@:)
	@[ ! -d doc ] && git clone ${repo} doc || :
	@cd doc && { \
		git reset --hard ; \
		git fetch --all ; \
		[ "$$(git branch --show-current)" != "master" ] && git checkout master || : ; \
		[ "${branch}" != "master" ] \
			&& { \
				{ \
					git branch -D ${branch} 2> /dev/null ; \
					git checkout ${branch} ; \
				} \
					&& git pull --ff-only origin ${branch} \
					|| { \
						>&2 echo "[!] The branch '${branch}' doesn't exist, checking out 'master' instead..." ; \
						git pull --ff-only origin master ; \
					} \
			} \
			|| git pull --ff-only origin master ; \
	} 1> /dev/null

## Install doc dependencies.
test-doc-install:
	@$(call help,$@:)
	@pip install --requirement doc/requirements.txt 1> /dev/null
	@pip install --editable .[dev] --upgrade 1> /dev/null

## Dry-build the doc.
test-doc-build:
	@$(call help,$@:)
	@sphinx-build -M dummy doc/source doc/build -n -q -W
