#!/bin/bash
set -e

OUTPUT="${1:-hsa_ledger_export_$(date +%Y%m%d_%H%M%S).csv}"

if [ ! -f "hsa_ledger.db" ]; then
    echo "Database not found. Run from project root or specify path." >&2
    exit 1
fi

uv run hsa-ledger export --csv "$OUTPUT"
echo "Exported to $OUTPUT"

TOTAL=$(sqlite3 hsa_ledger.db "SELECT COUNT(*) FROM hsa_receipts;")
UNREIMBURSED=$(sqlite3 hsa_ledger.db "SELECT COUNT(*) FROM hsa_receipts WHERE is_reimbursed = 0;")
ELIGIBLE=$(sqlite3 hsa_ledger.db "SELECT COALESCE(SUM(hsa_eligible_amount), 0) FROM hsa_receipts;")
UNREIM_AMT=$(sqlite3 hsa_ledger.db "SELECT COALESCE(SUM(hsa_eligible_amount), 0) FROM hsa_receipts WHERE is_reimbursed = 0;")

echo ""
echo "=== Summary ==="
echo "Total receipts:   $TOTAL"
echo "Unreimbursed:     $UNREIMBURSED"
echo "Total eligible:   \$$(printf "%.2f" "$ELIGIBLE")"
echo "Unreimbursed amt: \$$(printf "%.2f" "$UNREIM_AMT")"
echo "================"