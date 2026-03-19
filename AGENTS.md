# Repository Agent Notes

## Python command policy
For this repository, always use `uv` for Python-related commands.

- Use `uv run python ...` instead of `python ...`
- Use `uv run pytest ...` instead of `pytest ...`
- Use `uv run make ...` when invoking Make targets that execute Python tooling

This convention should be applied by default for future Codex/Claude/agent runs in this repo.

## Contribution workflow policy
After producing commits on a branch, create a Pull Request targeting `master` by default.

- Follow `CONTRIBUTING.md` when writing the PR.
- Include a clear text explanation of what changed and why.
- For functional changes, always update both:
  - package version in `setup.py` (SemVer bump)
  - `CHANGELOG.md` with the corresponding release notes
