#!/bin/bash
set -e

VAULT="${HSA_LEDGER_VAULT:-$PWD/hsa_vault}"
INBOX="$VAULT/inbox"

if [ ! -d "$INBOX" ]; then
    echo '{"status":"not_found","error":"Vault not initialized. Run: uv run hsa-ledger init"}' >&2
    exit 1
fi

python3 -c "
import json, os, sys

inbox = '$INBOX'
try:
    entries = []
    for f in os.listdir(inbox):
        fp = os.path.join(inbox, f)
        if os.path.isfile(fp) and not f.startswith('.'):
            entries.append({'name': f, 'size': os.path.getsize(fp)})
    print(json.dumps({'status': 'ok', 'files': entries, 'count': len(entries)}))
except FileNotFoundError:
    print(json.dumps({'status': 'not_found', 'error': 'Inbox directory does not exist'}))
    sys.exit(1)
"