clean:
	rm -rf build dist
	find . -name '*.pyc' -exec rm \{\} \;

test:
	flake8
	nosetests

# To activate the Piwik tracking, configure TRACKER_URL and TRACKER_IDSITE variables.
# For more information: https://github.com/openfisca/tracker/blob/master/README.md
api:
	COUNTRY_PACKAGE=openfisca_country_template gunicorn "openfisca_web_api_preview.app:create_app()" --bind localhost:5000 --workers 3
