#! /usr/bin/env bash

current_version=`python setup.py --version`

if ! git diff-index --quiet origin/master openfisca_core openfisca_web_api_preview
then
    if git rev-parse $current_version
    then
        set +x
        echo "Version $current_version already exists. Please update version number in setup.py before merging this branch into master."
        exit 1
    fi

    if git diff-index origin/master --quiet CHANGELOG.md
    then
        set +x
        echo "CHANGELOG.md has not been modified. Please update it before merging this branch into master."
        exit 1
    fi
fi
