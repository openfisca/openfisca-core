# Development process

## Branching model

OpenFisca-Core, OpenFisca-France and OpenFisca-Web-API (tend to) follow this Git branching model:

* the `master` branch is for releases
* the `next` branch is for preparing the next release
* feature branches can exist

See also: https://igor.io/2013/10/21/git-branching-model.html

## Versioning

Each Python package is versioned using [Semantic Versioning](http://semver.org/).

## Pull requests

To merge a pull-request into `next`, the tests must pass on the repository, using `make test`.

## Tests

See [tests.md](tests.md)
