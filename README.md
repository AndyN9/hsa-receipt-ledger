# HSA Receipt Ledger

![CI](https://github.com/AndyN9/hsa-receipt-ledger/actions/workflows/ci.yml/badge.svg)

Local-only MCP server + CLI for managing Health Savings Account receipts, invoices, and Explanation of Benefits (EOBs). LLM-guided extraction with conversational review, backed by a searchable SQLite ledger and a Streamlit dashboard.

## Requirements

- Python 3.11+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) engine (for image text extraction)
- sqlite3 (CLI for local bash scripts)

**macOS:** `brew install tesseract`

**Ubuntu/Debian:** `sudo apt install tesseract-ocr`

**Windows:** Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)

## Quick Start

```bash
uv sync                          # Install Python dependencies
uv run hsa-ledger init           # Create vault dirs and DB
uv run hsa-ledger --help         # See available commands
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `hsa-ledger init` | Create `hsa_vault/` directory structure and SQLite DB |
| `hsa-ledger status` | Show vault stats: record count, unreimbursed total, inbox files |
| `hsa-ledger clear --dry-run` | Preview what would be deleted |
| `hsa-ledger clear --force` | Destructive: delete all records, archive storage files |
| `hsa-ledger export --csv <path>` | Export ledger to CSV |
| `hsa-ledger ui` | Launch Streamlit dashboard with receipt previews at `http://localhost:8501` |
| `hsa-ledger mcp` | Run MCP server over stdio for LLM clients |

## OpenCode Integration

Register the MCP server in `opencode.json` (project level):

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "hsa-receipt-ledger": {
      "type": "local",
      "command": ["/full/path/to/.venv/bin/hsa-ledger", "mcp"]
    }
  }
}
```

Note: use the full absolute path (not `~`) — opencode runs the command directly, not through a shell.

## Workflow

1. Save a receipt PDF/photo into `hsa_vault/inbox/`
2. Ask the LLM: *"Process my new medical receipts"*
3. LLM calls `list_untracked_files`, then `extract_file_text`
4. LLM presents extracted fields for review; you confirm
5. LLM calls `insert_hsa_transaction` — file moves to `storage/`, record saved
6. Query via *"Find my dental costs from last year"* or browse in Streamlit

## Development

```bash
uv run pytest          # Run all tests
uv run pytest -v       # Verbose
uv run pytest --cov    # Coverage (if pytest-cov installed)
```

### CI/CD

Tests run automatically on every push to `main` via GitHub Actions. The workflow installs `uv`, syncs dependencies, and runs `uv run pytest`. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Tech Stack

| Layer | Technology |
|-------|------------|
| Runtime | Python 3.11+ |
| MCP Framework | FastMCP |
| PDF Text | `pypdf` |
| OCR | `pytesseract` (Tesseract) |
| HEIC Decode | `pyheif` |
| Database | SQLite (stdlib `sqlite3`) |
| CLI | `click` |
| Dashboard | `streamlit` + `pandas` |

## Security

- Zero-cloud — all data stays on the local machine
- Path traversal prevention on all file operations
- stdio-only MCP transport (no network exposure)
- All SQL queries parameterized
