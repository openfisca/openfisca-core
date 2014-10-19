check-tests-syntax:
	flake8 openfisca_core/

test: check-tests-syntax
	nosetests -x --with-doctest openfisca_core/

test-with-coverage:
	nosetests -x openfisca_core/ --with-coverage --cover-package=openfisca_core --cover-erase --cover-branches --cover-html
