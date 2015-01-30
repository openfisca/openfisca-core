TESTS_DIR="openfisca_core/tests/"

all: flake8 test

check-syntax-errors: clean-pyc
	@# This is a hack around flake8 not displaying E910 errors with the select option.
	test -z "`flake8 --first | grep E901`"

clean-pyc:
	find . -name '*.pyc' -exec rm \{\} \;

ctags:
	ctags --recurse=yes .

flake8: clean-pyc
	flake8

test: check-syntax-errors
	nosetests --with-doctest $(TESTS_DIR)

test-with-coverage:
	nosetests -v $(TESTS_DIR) --with-coverage --cover-package=openfisca_core --cover-erase --cover-branches --cover-html
