# Repository Agent Notes

## Python command policy
For this repository, always use `uv` for Python-related commands.

- Use `uv run python ...` instead of `python ...`
- Use `uv run pytest ...` instead of `pytest ...`
- Use `uv run make ...` when invoking Make targets that execute Python tooling

This convention should be applied by default for future Codex/Claude/agent runs in this repo.
