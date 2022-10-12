#! /usr/bin/env bash

git tag `python setup.py --version`
git push --tags || true  # update the repository version
