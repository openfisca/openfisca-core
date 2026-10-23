#! /usr/bin/env bash

if [[ ${GITHUB_REF#refs/heads/} == main ]]
then
    echo "::notice ::No need for a version check on main."
    exit 0
fi

if ! $(dirname "$BASH_SOURCE")/has-functional-changes.sh
then
    echo "::notice ::No need for a version update."
    exit 0
fi

current_version=$(uv version --short)

if [[ $current_version == "" ]]
then
    echo "::error ::The current version number was not fetched from pyproject. Exiting…"
    exit 1
fi

if git rev-parse --verify --quiet $current_version
then
    echo "::warning ::Version $current_version already exists in commit:"
    git --no-pager log -1 $current_version
    echo
    echo "::error ::Update the version number in pyproject.toml before merging this branch into main."
    echo "::notice ::Look at the CONTRIBUTING.md file to learn how the version number should be updated."
    exit 1
fi

if ! $(dirname "$BASH_SOURCE")/has-functional-changes.sh | grep --quiet CHANGELOG.md
then
    echo "::warning ::CHANGELOG.md has not been modified, while functional changes were made."
    echo "::error ::Explain what you changed before merging this branch into main."
    echo "::notice ::Look at the CONTRIBUTING.md file to learn how to write the changelog."
    exit 2
fi

echo "::notice ::Version and CHANGELOG updated. Looking good. Proceeding…"
