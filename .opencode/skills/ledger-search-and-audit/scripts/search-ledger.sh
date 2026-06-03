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

python3 -c "
import sqlite3, sys

conn = sqlite3.connect('$DB')
conn.row_factory = sqlite3.Row

conditions = []
params = []

query = '$QUERY'
start_date = '$START_DATE'
end_date = '$END_DATE'
category = '$CATEGORY'
reimbursed = '$REIMBURSED'

if query:
    conditions.append('(provider LIKE ? OR category LIKE ?)')
    params.extend([f'%{query}%', f'%{query}%'])

if start_date:
    conditions.append('transaction_date >= ?')
    params.append(start_date)

if end_date:
    conditions.append('transaction_date <= ?')
    params.append(end_date)

if category:
    conditions.append('category = ?')
    params.append(category)

if reimbursed:
    conditions.append('is_reimbursed = ?')
    params.append(int(reimbursed))

sql = 'SELECT id, provider, patient_name, transaction_date, total_amount, hsa_eligible_amount, category, is_reimbursed, reimbursement_date FROM hsa_receipts'
if conditions:
    sql += ' WHERE ' + ' AND '.join(conditions)
sql += ' ORDER BY transaction_date DESC'

cursor = conn.execute(sql, params)
rows = cursor.fetchall()

if not rows:
    print('No matching records found.')
    sys.exit(0)

headers = ['id', 'provider', 'patient_name', 'transaction_date', 'total_amount', 'hsa_eligible_amount', 'category', 'is_reimbursed', 'reimbursement_date']
col_widths = {h: len(h) for h in headers}
for r in rows:
    for h in headers:
        val = str(r[h]) if r[h] is not None else 'NULL'
        col_widths[h] = max(col_widths[h], len(val))

sep = '  '.join(h.ljust(col_widths[h]) for h in headers)
print(sep)
print('  '.join('-' * col_widths[h] for h in headers))

total_amt = 0.0
total_eligible = 0.0
for r in rows:
    vals = []
    for h in headers:
        val = str(r[h]) if r[h] is not None else 'NULL'
        vals.append(val.ljust(col_widths[h]))
    print('  '.join(vals))
    total_amt += r['total_amount'] or 0
    total_eligible += r['hsa_eligible_amount'] or 0

total_count = len(rows)
unreimbursed = sum(1 for r in rows if r['is_reimbursed'] == 0)
print()
print(f'Records: {total_count}  |  Unreimbursed: {unreimbursed}')
print(f'Total: \${total_amt:.2f}  |  HSA Eligible: \${total_eligible:.2f}')

conn.close()
"