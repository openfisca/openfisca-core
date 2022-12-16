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


## Manual actions to test before CI

Everything is done by the CI but if you want to test it locally, here is how to do it.

Do the following in the project root folder:

- Auto-update `.conda/meta.yaml` with last infos from pypi by running:
    - `python .github/get_pypi_info.py -p OpenFisca-Core`

- Build package:
    - `conda install -c anaconda conda-build anaconda-client` (`conda-build` to build the package and [anaconda-client](https://github.com/Anaconda-Platform/anaconda-client) to push the package to anaconda.org)
    - `conda build -c conda-forge .conda`

 - Upload the package to Anaconda.org, but DON'T do it if you don't want to publish your locally built package as official openfisca-core library:
    - `anaconda login`
    - `anaconda upload openfisca-core-<VERSION>-py_0.tar.bz2`

## Test with Docker

To check if a local package work before publication:
```
docker run -i -t -v /media/data-nvme/dev/anaconda3/conda-bld/:/conda-bld continuumio/anaconda3 /bin/bash
conda install -c /conda-bld/noarch/openfisca-core-dev-38.0.1-py_0.tar.bz2 openfisca-core-dev
openfisca -h
```

To check if the published package work:
```
docker run -i -t continuumio/anaconda3 /bin/bash
conda install -c openfisca -c conda-forge openfisca-core-dev
openfisca -h
```
