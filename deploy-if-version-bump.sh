#!/bin/sh

set -e
if [ $PY_VERSION = "2" ]; then
  if ! git rev-parse `python setup.py --version` 2>/dev/null ; then
      git tag `python setup.py --version`
      git push --tags  # update the repository version
      python setup.py bdist_wheel  # build this package in the dist directory
      twine upload dist/* --username $PYPI_USERNAME --password $PYPI_PASSWORD  # publish
      ssh -o StrictHostKeyChecking=no deploy-api@fr.openfisca.org
  else
      echo "No deployment - Only non-functional elements were modified in this change"
  fi
fi

if [ $PY_VERSION = "3" ]; then
  python setup.py bdist_wheel  # build this package in the dist directory
  if ! twine upload dist/* --username $PYPI_USERNAME --password $PYPI_PASSWORD; then  # publish
    echo "Could not upload this package version on Pypi. This usually means that the version already exists, and that only non-functional elements were modified in this change. If this it not the case, check the error message above."
  fi
fi
