---
name: ledger-search-and-audit
description: Searches the HSA ledger and audits receipts. Use when a user says "find receipts", "search my ledger", "show me dental expenses", "audit my HSA", or "what did I spend on X". Use when you need to query the database by provider, date, category, or reimbursement status.
---

# Ledger Search & Audit

Search and analyze the HSA receipt ledger. Translates natural language queries into structured search parameters, presents results clearly, and flags data quality issues.

## When to Use

- User asks to find specific receipts or expenses
- User wants to audit spending by category, provider, or time period
- User needs to verify data quality (missing fields, anomalies)
- User wants to check reimbursement status before requesting an HSA distribution

## Workflow

### Step 1: Parse Intent

Extract search parameters from the user's natural language request:

| User says | Parameters |
|-----------|-----------|
| "dental costs from last year" | `category=dental`, `start_date=2025-01-01`, `end_date=2025-12-31` |
| "anything from Quest Diagnostics" | `query=Quest` |
| "unreimbursed expenses" | `is_reimbursed=0` |
| "March 2024 lab work" | `start_date=2024-03-01`, `end_date=2024-03-31`, `category=Lab Work` |

### Step 2: Search the Ledger

Call `search_ledger` MCP tool with the parsed parameters:

```
search_ledger(
    query="",
    start_date="2025-01-01",
    end_date="2025-12-31",
    category="dental",
    is_reimbursed=None
)
```

### Step 3: Present Results

Format results as a table:

```
 ID       Provider         Date        Total   Eligible  Category   Reimbursed
 ─────── ──────────────── ────────── ──────── ───────── ────────── ──────────
 abc123  Dr. Smith Dental 2025-03-15  $250.00   $250.00  Dental     No
 def456  City Ortho       2025-06-01  $500.00   $500.00  Dental     Yes (2025-07-01)
...
 ─────── ──────────────── ────────── ──────── ───────── ────────── ──────────
                                    Total: $750.00  Eligible: $750.00
```

Include:
- Total and HSA-eligible subtotals
- Number of results
- File paths for reference (user can open locally)

### Step 4: Run Audit Checks

After presenting results, check for data quality issues:

- **Missing patient_name:** Records where `patient_name` is NULL
- **Total > eligible:** Records where `total_amount > hsa_eligible_amount` (may indicate non-qualifying portion)
- **Missing category:** Uncategorized expenses
- **Unreimbursed eligible expenses:** Summarize total unreimbursed amount
- **Orphaned files:** Receipt files in `hsa_vault/storage/` not linked to any record (call `list_untracked_files` and cross-reference)

### Step 5: Offer Follow-ups

After displaying results, offer to:

- Mark one or more receipts as reimbursed via `update_reimbursement_status`
- Export the result set (see Export & Tax Prep skill)
- Filter further or refine the search
- Show the receipt file itself (open from the local path)

## Scripts

### search-ledger.sh

Query the database directly from the terminal:

```bash
# All records
bash .opencode/skills/ledger-search-and-audit/scripts/search-ledger.sh

# By provider
bash .opencode/skills/ledger-search-and-audit/scripts/search-ledger.sh "Quest"

# By date range
bash .opencode/skills/ledger-search-and-audit/scripts/search-ledger.sh "" "2025-01-01" "2025-12-31"

# By category and reimbursed status
bash .opencode/skills/ledger-search-and-audit/scripts/search-ledger.sh "" "" "" "Dental" "0"
```

Arguments: `[query] [start_date] [end_date] [category] [is_reimbursed]`

## Troubleshooting

- **Search returns no results:** Expand the date range, try a broader query, or check that the database is initialized.
- **Missing expected records:** Verify with `uv run hsa-ledger status` to see total record count.
