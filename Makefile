clean:
	rm -rf build dist
	find . -name '*.pyc' -exec rm \{\} \;

test:
	flake8
	nosetests
