#!/bin/bash
set -e

VAULT="${HSA_LEDGER_VAULT:-$PWD/hsa_vault}"
INBOX="$VAULT/inbox"

if [ ! -d "$INBOX" ]; then
    echo "Vault not initialized. Run: uv run hsa-ledger init" >&2
    exit 1
fi

FILES=("$INBOX"/*)
if [ ! -e "${FILES[0]}" ]; then
    echo '{"status":"empty","files":[],"count":0}'
    exit 0
fi

RESULTS=()
for f in "$INBOX"/*; do
    [ -f "$f" ] || continue
    name=$(basename "$f")
    size=$(stat -c%s "$f" 2>/dev/null || stat -f%z "$f" 2>/dev/null)
    RESULTS+=("{\"name\":\"$name\",\"size\":$size}")
done

echo "{\"status\":\"ok\",\"files\":[$(IFS=,; echo "${RESULTS[*]}")],\"count\":${#RESULTS[@]}}"