# Publish Open-Fisca-Core to conda

We use two systems to publish to conda:
- A fully automatic in Open-Fisca-Core CI that publish to an "openfisca" channel. See below for more information.
- A more complex in Conda-Forge CI, that publish to Conda-Forge. See https://www.youtube.com/watch?v=N2XwK9BkJpA for an introduction to Conda-Forge, and https://github.com/openfisca/openfisca-core-feedstock for the project use for Conda-Forge.

We use both as with conda-forge our users get an easiest way to install and use openfisca-core : conda-forge is the default channels in Anaconda and it allow publishing packages that depend on openfisca-core to conda-forge.

## Automatic upload

The CI automaticaly upload the PyPi package, see the `.github/workflow.yml`, step `publish-to-conda`.

## Manual actions for first time publishing

- Create an account on https://anaconda.org.
- Create a token on https://anaconda.org/openfisca/settings/access with _Allow write access to the API site_. Warning, it expire on 2023/01/13.
- Put the token in a CI env variable ANACONDA_TOKEN.

## Manual actions before CI configuration

To create the package you can do the following in the project root folder:

- Edit `.conda/meta.yaml` and update it if needed:
    - Version number
    - Hash SHA256
    - Package URL on PyPi

- Build & Upload package:
    - `conda install -c anaconda conda-build anaconda-client`
    - `conda build .conda`
    - `anaconda login`
    - `anaconda upload openfisca-core-<VERSION>-py_0.tar.bz2`
