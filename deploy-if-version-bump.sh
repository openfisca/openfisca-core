#!/bin/sh

set -e
if ! git rev-parse `python setup.py --version` 2>/dev/null ; then
    git tag `python setup.py --version`
    git push --tags
    python setup.py bdist_wheel
    twine upload dist/* --username openfisca-bot --password fakepassword
    ssh deploy-new-api@api-test.openfisca.fr
else
    echo "No deployment - Only non-functional elements were modified in this change"
fi
