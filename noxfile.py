import nox

# nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = ["test"]
python_versions = ["3.7.11", "3.8.12", "3.9.7"]
numpy_versions = ["1.18.5", "1.19.5", "1.20.3", "1.21.2"]


@nox.session(python = python_versions)
@nox.parametrize("numpy", numpy_versions)
def test(session, numpy):
    session.install(".[dev]")
    session.install(f"numpy=={numpy}")
    session.run("pytest", "-qx", *session.posargs)
