all: test

uninstall:
	pip freeze | grep -v "^-e" | xargs pip uninstall -y

install:
	pip install --upgrade pip twine wheel
	pip install --editable .[dev] --upgrade

clean:
	rm -rf build dist
	find . -name '*.pyc' -exec rm \{\} \;

check-syntax-errors:
	python -m compileall -q .

check-style:
	@# Do not analyse .gitignored files.
	@# `make` needs `$$` to output `$`. Ref: http://stackoverflow.com/questions/2382764.
	flake8 `git ls-files | grep "\.py$$"`

format-style:
	@# Do not analyse .gitignored files.
	@# `make` needs `$$` to output `$`. Ref: http://stackoverflow.com/questions/2382764.
	autopep8 `git ls-files | grep "\.py$$"`

test: clean check-syntax-errors check-style
	pytest

api:
	openfisca serve --country-package openfisca_country_template --extensions openfisca_extension_template
