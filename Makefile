test:
	nosetests -x openfisca_core/tests

test-with-cover:
	nosetests -x openfisca_core/tests --with-coverage --cover-package=openfisca_core --cover-erase --cover-branches --cover-html
