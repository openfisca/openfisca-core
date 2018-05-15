#!/bin/sh

set -e

echo "**Publishing on Pypi**"

python setup.py bdist_wheel  # build this package in the dist directory
if ! twine upload dist/* --username $PYPI_USERNAME --password $PYPI_PASSWORD; then  # publish
  echo "Could not upload this package version on Pypi. This usually means that the version already exists, and that only non-functional elements were modified in this change. If this it not the case, check the error message above."
fi

echo "**Publishing Github tag and deploying the web API**"

git fetch
if ! git rev-parse --quiet `python setup.py --version` 2>/dev/null ; then
    git tag `python setup.py --version`
    git push --tags  # update the repository version
    ssh -o StrictHostKeyChecking=no deploy-api@fr.openfisca.org
else
    echo "This version has already been published on Github."
fi

