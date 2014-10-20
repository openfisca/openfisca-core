check-syntax-errors: clean-pyc
	@# This is a hack around flake8 not displaying E910 errors with the select option.
	test -z "`flake8 --first | grep E901`"

clean-pyc:
	find -name '*.pyc' -exec rm \{\} \;

ctags:
	ctags --recurse=yes .

flake8: clean-pyc
	flake8

test: check-syntax-errors
	nosetests -v --with-doctest openfisca_core/

test-with-coverage:
	nosetests -v openfisca_core/ --with-coverage --cover-package=openfisca_core --cover-erase --cover-branches --cover-html
