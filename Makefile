TESTS_DIR=openfisca_core

all: flake8 test

check-syntax-errors:
	@# This is a hack around flake8 not displaying E910 errors with the select option.
	@# Do not analyse .gitignored files.
	@# `make` needs `$$` to output `$`. Ref: http://stackoverflow.com/questions/2382764.
	test -z "`flake8 --first $(shell git ls-files | grep "\.py$$") | grep E901`"

clean: clean-mo clean-pyc
	rm -rf build dist

clean-mo:
	find . -name '*.mo' -exec rm \{\} \;

clean-pyc:
	find . -name '*.pyc' -exec rm \{\} \;

ctags:
	ctags --recurse=yes .

flake8: clean-pyc
	flake8

test: check-syntax-errors
	nosetests $(TESTS_DIR) --exe --stop --with-doctest

test-ci: check-syntax-errors
	nosetests $(TESTS_DIR) --exe --with-doctest

test-with-coverage:
	nosetests $(TESTS_DIR) --exe --stop --with-coverage --cover-package=openfisca_core --cover-erase --cover-branches --cover-html
