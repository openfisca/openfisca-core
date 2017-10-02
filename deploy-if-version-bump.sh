#!/bin/sh

set -e
if ! git rev-parse `python setup.py --version` 2>/dev/null ; then
    git tag `python setup.py --version`
    git push --tags  # update the repository version
    python setup.py bdist_wheel  # build this package in the dist directory
    twine upload dist/* --username $PYPI_USERNAME --password $PYPI_PASSWORD  # publish
    ssh deploy-new-api@fr.openfisca.org
else
    echo "No deployment - Only non-functional elements were modified in this change"
fi
