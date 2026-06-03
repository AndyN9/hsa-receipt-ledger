---
name: export-and-tax-prep
description: Exports receipts and generates tax-prep summaries. Use when a user says "export my receipts", "generate HSA distribution report", "prepare for tax filing", "year-end summary", or "show me totals by category".
---

# Export & Tax Prep

Generate CSV exports and HSA tax preparation reports. Helps users gather documentation for IRS Form 8889 (HSA Distributions) and maintain records for future tax filings.

## When to Use

- User needs a CSV export of all or filtered receipts
- User wants a year-end or period summary for tax filing
- User needs to verify total HSA-eligible distributions vs reimbursements
- User wants to identify outstanding unreimbursed expenses

## Workflow

### Step 1: Determine Scope

Ask the user what they want to export:

- **All records** — full ledger export
- **By year** — e.g., "2025 tax year"
- **By category** — e.g., "all dental expenses"
- **Unreimbursed only** — expenses not yet reimbursed from HSA
- **Reimbursed only** — already claimed distributions

### Step 2: Export CSV

Call the CLI export command:

```bash
uv run hsa-ledger export --csv hsa_ledger_export_2025.csv
```

Or use the skill script:

```bash
bash .opencode/skills/export-and-tax-prep/scripts/export-csv.sh hsa_ledger_export_2025.csv
```

For filtered exports, use `search_ledger` via MCP first, then export manually from the results.

### Step 3: Generate Summary Report

After export, compute and present a summary:

```
=== HSA Ledger Summary ===
Reporting period: 2025-01-01 to 2025-12-31
Total receipts:          12
Total spent:             $4,250.00
HSA-eligible total:      $3,890.00
Unreimbursed eligible:   $1,200.00  (needs HSA distribution)
Reimbursed total:        $2,690.00

By Category:
  Dental:         $950.00  (24.4%)
  Lab Work:       $890.00  (22.9%)
  Pharmacy:       $720.00  (18.5%)
  Vision:         $680.00  (17.5%)
  Doctor Visit:   $650.00  (16.7%)

Records missing patient_name: 2
Records missing category:     0
```

### Step 4: Identify Documentation Gaps

Flag records that may cause issues during an IRS audit:

- Receipts with no extracted text (OCR may have failed)
- Records with `total_amount > hsa_eligible_amount` — the difference is not tax-free
- Records with missing `patient_name` — unclear who received the service
- Reimbursed records with no `reimbursement_date`

### Step 5: Offer Next Steps

- Save the CSV to a known location for tax preparer
- Print or open the report
- Generate individual receipt summaries as needed
- Mark unreimbursed expenses as reimbursed after taking an HSA distribution

## Scripts

### export-csv.sh

Export all records to CSV with an auto-generated summary:

```bash
# Default: hsa_ledger_export_YYYYMMDD_HHMMSS.csv
bash .opencode/skills/export-and-tax-prep/scripts/export-csv.sh

# Custom output path
bash .opencode/skills/export-and-tax-prep/scripts/export-csv.sh /path/to/output.csv
```

The script exports the CSV and prints a summary with totals, counts, and unreimbursed amounts.

## Troubleshooting

- **Export fails:** Verify the database exists (`uv run hsa-ledger status`). Run `uv run hsa-ledger init` if needed.
- **No records to export:** Confirm the ledger has data. Use the Ledger Search & Audit skill to check.
- **CSV empty but DB has data:** Check permissions on the output directory.
