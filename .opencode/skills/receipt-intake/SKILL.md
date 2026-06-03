---
name: receipt-intake
description: Processes new HSA receipts from the inbox using MCP tools. Use when a user says "process my receipts", "scan inbox", "add a receipt", "new medical bill", or drops files into hsa_vault/inbox/. Use when you need to OCR a receipt and insert it into the ledger.
---

# Receipt Intake

End-to-end workflow for adding new HSA receipts. The LLM acts as a conversational data-entry assistant — extracting structured fields from OCR output, presenting a preview, and inserting into the ledger only after user confirmation.

## When to Use

- User drops receipt files (PDF, PNG, JPG, HEIC) into `hsa_vault/inbox/`
- User asks to process new receipts
- A previous OCR/extraction step failed or needs retry
- User wants to verify extracted data before committing

## Workflow

### Step 1: Verify Vault State

Check that the vault is initialized:

```bash
ls hsa_vault/inbox/ hsa_vault/storage/ hsa_vault/archive/ 2>/dev/null || uv run hsa-ledger init
```

Or check via status:

```bash
uv run hsa-ledger status
```

### Step 2: List Untracked Files

Call the MCP tool `list_untracked_files` to discover new files. Present the filenames to the user and ask which to process (or confirm all).

### Step 3: Extract Text

For each untracked file, call `extract_file_text(file_name="...")` via MCP. Handle the result:

- **Success:** Present the raw extracted text to the user. If text is garbled or empty, warn that OCR quality may be low.
- **Error ("File not found"):** The file may have been moved. Re-run `list_untracked_files`.
- **Unsupported format:** Inform the user which formats are supported (PDF, PNG, JPG, HEIC).

### Step 4: Present Extracted Data for Confirmation

Parse the raw text and present a structured preview:

```
Found receipt: receipt_001.jpg
Provider:      Quest Diagnostics
Date:          2024-03-15
Total:         $187.50
Eligible:      $187.50
Category:      Lab Work
Patient:       Self

This file's SHA-256 hash does not match any existing record.
Insert this transaction?
```

Ask the user to confirm or correct any field before inserting.

### Step 5: Insert Transaction

On confirmation, call `insert_hsa_transaction` via MCP with the confirmed fields. Handle responses:

- **Success:** `"Inserted transaction with ID: <hash>"` — confirm to the user.
- **Conflict (duplicate):** Show the existing record and ask: insert anyway (`force=True`) or skip?
- **Missing fields error:** Re-prompt the user for the missing fields.

### Step 6: Repeat

Continue with remaining untracked files. When done, summarize:

```
Processed 3 receipts:
  ✅ receipt_001.jpg — Quest Diagnostics, $187.50
  ✅ receipt_002.pdf — Walgreens Pharmacy, $45.99
  ⏭️  receipt_003.heic — skipped (user declined)
```

## Scripts

### process-inbox.sh

Check vault state and list inbox files as JSON:

```bash
bash .opencode/skills/receipt-intake/scripts/process-inbox.sh
```

Output:
```json
{"status":"ok","files":[{"name":"receipt_001.jpg","size":245760}],"count":1}
```

## Troubleshooting

- **OCR returns empty text:** The image may be scanned at low resolution. Try re-saving at 300+ DPI.
- **HEIC not supported:** Install `pyheif` with `uv add pyheif`. On Linux you may need `libheif` system package.
- **Tesseract not found:** Install Tesseract OCR: `apt install tesseract-ocr` (Linux), `brew install tesseract` (macOS).
- **File shows as untracked but extraction fails:** The file may be corrupt. Ask the user to re-save it.
