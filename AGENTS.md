# AGENTS.md — HSA Receipt Ledger

## Overview

A local-only MCP server + CLI for managing HSA receipts. Python project using FastMCP, SQLite, Streamlit, and Tesseract OCR.

## Commands

```bash
uv run pytest              # Run all tests (must use uv run — system Python lacks deps)
uv run hsa-ledger --help   # CLI help
uv run hsa-ledger init     # Initialize vault dirs and DB
uv run hsa-ledger mcp      # Start MCP server (stdio)
uv run hsa-ledger ui       # Launch Streamlit dashboard
```

Or activate the venv first to avoid the `uv run` prefix:

```bash
source .venv/bin/activate
pytest
hsa-ledger --help
```

## Key Files

| File | Purpose |
|------|---------|
| `src/hsa_ledger/server.py` | 5 MCP tools (FastMCP) |
| `src/hsa_ledger/database.py` | SQLite CRUD, search, stats |
| `src/hsa_ledger/vault.py` | File inbox/storage/archive operations |
| `src/hsa_ledger/extractor.py` | PDF text, OCR, HEIC decode |
| `src/hsa_ledger/__main__.py` | Click CLI entry point |
| `src/hsa_ledger/ui.py` | Streamlit dashboard with receipt image previews |
| `tests/test_ui.py` | UI helper tests (`_is_image_path`) |

## Rules

- Run `uv run pytest` before and after changes.
- Use `uv add <pkg>` for new dependencies, then update `pyproject.toml`.
- Tests go in `tests/test_<module>.py`, fixtures in `tests/conftest.py`.
- MCP tool functions in `server.py` must return strings (FastMCP serializes).
- New SQL queries must be parameterized — no string formatting.
- Path traversal check required on any user-supplied file name.

## CI/CD

- Ensure CI passes before pushing to `main` — GitHub Actions runs `uv run pytest` on every push
- CI is purely a test gate; no secrets or services are required
