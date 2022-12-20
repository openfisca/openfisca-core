"""Nox config file."""

import nox

nox.options.reuse_existing_virtualenvs = True
nox.options.stop_on_first_error = True


@nox.session(python = ("3.9", "3.8", "3.7"), tags = ("lint", "style"))
@nox.parametrize("numpy", ("1.23", "1.22", "1.21"))
def style(session, numpy):
    """Run tests."""

    if session.python == "3.7" and numpy == "1.22":
        return

    session.install("--upgrade", "pip")
    session.install(".[dev]")
    session.install(f"numpy=={numpy}")
    session.run("make", "check-style", external = True)


@nox.session(python = ("3.9", "3.8", "3.7"), tags = ("lint", "docs"))
@nox.parametrize("numpy", ("1.23", "1.22", "1.21"))
def docs(session, numpy):
    """Run tests."""

    if session.python == "3.7" and numpy == "1.22":
        return

    session.install("--upgrade", "pip")
    session.install(".[dev]")
    session.install(f"numpy=={numpy}")
    session.run("make", "lint-doc", external = True)


@nox.session(python = ("3.9", "3.8", "3.7"), tags = ("lint", "mypy"))
@nox.parametrize("numpy", ("1.23", "1.22", "1.21"))
def mypy(session, numpy):
    """Run tests."""

    if session.python == "3.7" and numpy == "1.22":
        return

    session.install("--upgrade", "pip")
    session.install(".[dev]")
    session.install(f"numpy=={numpy}")
    session.run("make", "check-types", external = True)


@nox.session(python = ("3.9", "3.8", "3.7"), tags = ("lint", "mypy-hxc"))
@nox.parametrize("numpy", ("1.23", "1.22", "1.21"))
def mypy_hxc(session, numpy):
    """Run tests."""

    if session.python == "3.7" and numpy == "1.22":
        return

    session.install("--upgrade", "pip")
    session.install(".[dev]")
    session.install(f"numpy=={numpy}")
    session.run("make", "lint-typing-strict", external = True)


@nox.session(python = ("3.9", "3.8", "3.7"), tags = ("test", "test-core"))
@nox.parametrize("numpy", ("1.23", "1.22", "1.21"))
def test_core(session, numpy):
    """Run tests."""

    if session.python == "3.7" and numpy == "1.22":
        return

    session.install("--upgrade", "pip")
    session.install(".[dev]")
    session.install(f"numpy=={numpy}")
    session.install("--no-deps", "openfisca-country-template")
    session.install("--no-deps", "openfisca-extension-template")
    session.run("make", "test-core", external = True)


@nox.session(python = ("3.9", "3.8", "3.7"), tags = ("test", "test-country"))
@nox.parametrize("numpy", ("1.23", "1.22", "1.21"))
def test_country(session, numpy):
    """Run tests."""

    if session.python == "3.7" and numpy == "1.22":
        return

    session.install("--upgrade", "pip")
    session.install(".[dev]")
    session.install(f"numpy=={numpy}")
    session.install("--no-deps", "openfisca-country-template")
    session.install("--no-deps", "openfisca-extension-template")
    session.run("make", "test-country", external = True)


@nox.session(python = ("3.9", "3.8", "3.7"), tags = ("test", "test-extension"))
@nox.parametrize("numpy", ("1.23", "1.22", "1.21"))
def test_extension(session, numpy):
    """Run tests."""

    if session.python == "3.7" and numpy == "1.22":
        return

    session.install("--upgrade", "pip")
    session.install(".[dev]")
    session.install(f"numpy=={numpy}")
    session.install("--no-deps", "openfisca-country-template")
    session.install("--no-deps", "openfisca-extension-template")
    session.run("make", "test-extension", external = True)
