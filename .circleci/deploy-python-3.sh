#!/bin/sh

set -e

VERSION_CHANGE_TRIGGERS="setup.py MANIFEST.in openfisca_core openfisca_web_api_preview"

if git diff-index --quiet HEAD^ -- $VERSION_CHANGE_TRIGGERS ":(exclude)*.md"
then
    echo "No deployment - Only non-functional elements were modified in this change"
    exit 0  # there are no changes at all, the version is correct
fi


python setup.py bdist_wheel  # build this package in the dist directory
twine upload dist/* --username $PYPI_USERNAME --password $PYPI_PASSWORD  # publish
