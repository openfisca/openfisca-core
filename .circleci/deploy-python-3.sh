#!/bin/sh

set -e

python setup.py bdist_wheel  # build this package in the dist directory
if ! twine upload dist/* --username $PYPI_USERNAME --password $PYPI_PASSWORD; then  # publish
  echo "Could not upload this package version on Pypi. This usually means that the version already exists, and that only non-functional elements were modified in this change. If this it not the case, check the error message above."
fi
