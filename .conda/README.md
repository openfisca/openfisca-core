# Publish OpenFisca-Core to conda

We use two systems to publish to conda:
- A fully automatic in OpenFisca-Core CI that publishes to an `openfisca` channel. See below for more information.
- A more complex in Conda-Forge CI, that publishes to [Conda-Forge](https://conda-forge.org). See this [YouTube video](https://www.youtube.com/watch?v=N2XwK9BkJpA) as an introduction to Conda-Forge, and [openfisca-core-feedstock repository](https://github.com/openfisca/openfisca-core-feedstock) for the project publishing process on Conda-Forge.

We use both channels. With conda-forge users get an easier way to install and use openfisca-core: conda-forge is the default channel in Anaconda and it allows for publishing packages that depend on openfisca-core to conda-forge.


## Automatic upload

The CI automatically uploads the PyPi package; see the `.github/workflow.yml`, step `publish-to-conda`.

## Manual actions for first time publishing

- Create an account on https://anaconda.org.
- Create a token on https://anaconda.org/openfisca/settings/access with `Allow write access to the API site`. Warning, it expires on 2023/01/13.

- Put the token in a CI environment variable named `ANACONDA_TOKEN`.


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
