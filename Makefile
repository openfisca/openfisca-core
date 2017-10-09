clean:
	rm -rf build dist
	find . -name '*.pyc' -exec rm \{\} \;

test:
	flake8
	nosetests

api:
	openfisca-serve -c openfisca_country_template -e openfisca_extension_template
