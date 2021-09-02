import nox

nox.options.reuse_existing_virtualenvs = True
py_versions = ["3.7.11", "3.8.12", "3.9.7"]
np_versions = ["1.18.5", "1.19.5", "1.20.3", "1.21.2"]


@nox.session(python = py_versions)
@nox.parametrize("numpy", np_versions, ids = np_versions)
def test(session, numpy):
    session.install("-e", ".[dev]")
    session.install("invoke")
    session.install("pytest-parallel-39")
    session.install(f"numpy=={numpy}")
    session.run("inv", "test", " ".join(session.posargs))
