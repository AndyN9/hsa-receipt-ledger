#!/bin/bash
set -e

DB="${HSA_LEDGER_DB:-$PWD/hsa_ledger.db}"

if [ ! -f "$DB" ]; then
    echo "Database not found at $DB. Run: uv run hsa-ledger init" >&2
    exit 1
fi

QUERY="${1:-}"
START_DATE="${2:-}"
END_DATE="${3:-}"
CATEGORY="${4:-}"
REIMBURSED="${5:-}"

SQL="SELECT id, provider, patient_name, transaction_date, total_amount, hsa_eligible_amount, category, is_reimbursed, reimbursement_date FROM hsa_receipts"
CONDITIONS=()
PARAMS=()

if [ -n "$QUERY" ]; then
    CONDITIONS+=("(provider LIKE '%' || ? || '%' OR category LIKE '%' || ? || '%')")
    PARAMS+=("$QUERY" "$QUERY")
fi
if [ -n "$START_DATE" ]; then
    CONDITIONS+=("transaction_date >= ?")
    PARAMS+=("$START_DATE")
fi
if [ -n "$END_DATE" ]; then
    CONDITIONS+=("transaction_date <= ?")
    PARAMS+=("$END_DATE")
fi
if [ -n "$CATEGORY" ]; then
    CONDITIONS+=("category = ?")
    PARAMS+=("$CATEGORY")
fi
if [ -n "$REIMBURSED" ]; then
    CONDITIONS+=("is_reimbursed = $REIMBURSED")
fi

if [ ${#CONDITIONS[@]} -gt 0 ]; then
    SQL="$SQL WHERE $(IFS=' AND '; echo "${CONDITIONS[*]}")"
fi
SQL="$SQL ORDER BY transaction_date DESC;"

sqlite3 -header -column "$DB" "$SQL" "${PARAMS[@]}"