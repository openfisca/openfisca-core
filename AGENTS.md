# Agent instructions (OpenFisca-Core)

This file is read by Cursor, Claude, Antigravity, and other agentic tools. Follow it when working in this repo.

## Pre-push checklist

**Before every `git push`**, run the full lint and fix any issues, then push.

1. **Lint** (from repo root):
   ```bash
   make clean check-syntax-errors check-style lint-doc PYTHON=.venv/bin/python
   ```
   - Fix any failures (e.g. `black`, `isort`, `flake8`, `codespell`). Use `make format-style` or run the formatter on the reported files if needed.
2. **Then** stage, commit (if there are new changes from fixes), and push.

Do not push without having run lint successfully unless the user explicitly asks to skip it.
