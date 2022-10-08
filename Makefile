all: install format test build changelog

documentation:
	jb clean docs
	jb build docs

format:
	black . -l 79

install:
	pip install -e .

test:
	coverage run -a --branch -m pytest tests
	coverage xml -i

build:
	python setup.py sdist bdist_wheel

changelog:
	build-changelog changelog.yaml --output changelog.yaml --update-last-date --start-from 0.1.0 --append-file changelog_entry.yaml
	build-changelog changelog.yaml --org PolicyEngine --repo policyengine-core --output CHANGELOG.md --template .github/changelog_template.md
	bump-version changelog.yaml setup.py
	rm changelog_entry.yaml || true
	touch changelog_entry.yaml