import os
import json
import hashlib
import sqlite3
from mcp.server.fastmcp import FastMCP

from hsa_ledger.database import (
    init_db,
    insert_transaction,
    get_record_by_hash,
    search_ledger as db_search_ledger,
    update_reimbursement_status as db_update_reimbursement,
)
from hsa_ledger.vault import list_untracked_files as vault_list_untracked, move_to_storage
from hsa_ledger.extractor import extract_file_text as extractor_extract_text

mcp = FastMCP("HSA-Receipt-Ledger")

_conn: sqlite3.Connection | None = None
_inbox_dir: str = ""
_storage_dir: str = ""


def _validate_basename(name: str) -> None:
    if "/" in name or "\\" in name or name.startswith("."):
        raise ValueError(f"Invalid file name: {name}")


def init_server(vault_base: str, db_path: str) -> None:
    global _conn, _inbox_dir, _storage_dir
    _conn = init_db(db_path)
    _inbox_dir = os.path.join(vault_base, "inbox")
    _storage_dir = os.path.join(vault_base, "storage")


@mcp.tool()
def list_untracked_files() -> list[str]:
    return vault_list_untracked(_inbox_dir, _conn)


@mcp.tool()
def extract_file_text(file_name: str) -> str:
    try:
        _validate_basename(file_name)
    except ValueError as e:
        return str(e)

    file_path = os.path.join(_inbox_dir, file_name)
    try:
        return extractor_extract_text(file_path)
    except (FileNotFoundError, OSError):
        return f"File not found: {file_name}"
    except ValueError as e:
        return str(e)


@mcp.tool()
def insert_hsa_transaction(
    file_name: str,
    provider: str,
    patient_name: str | None = None,
    transaction_date: str | None = None,
    total_amount: float | None = None,
    hsa_eligible_amount: float | None = None,
    category: str | None = None,
    extracted_text: str | None = None,
    force: bool = False,
) -> str:
    missing = []
    if not provider:
        missing.append("provider")
    if not transaction_date:
        missing.append("transaction_date")
    if total_amount is None:
        missing.append("total_amount")
    if hsa_eligible_amount is None:
        missing.append("hsa_eligible_amount")
    if missing:
        return f"Missing required fields: {', '.join(missing)}"

    try:
        _validate_basename(file_name)
    except ValueError as e:
        return str(e)

    file_path = os.path.join(_inbox_dir, file_name)

    try:
        with open(file_path, "rb") as f:
            content = f.read()
    except (FileNotFoundError, OSError) as e:
        return f"File not found: {file_name}"

    file_hash = hashlib.sha256(content).hexdigest()

    existing = get_record_by_hash(_conn, file_hash)
    if existing and not force:
        return (
            f"CONFLICT: This file is a duplicate of:\n"
            f"  Receipt #{existing['id']} — {existing['provider']}, "
            f"{existing['transaction_date']}, ${existing['total_amount']:.2f}\n"
            f"Use force=True to insert anyway."
        )

    try:
        storage_path = move_to_storage(
            _inbox_dir, _storage_dir, file_name, file_hash
        )
    except (FileNotFoundError, OSError, ValueError) as e:
        return str(e)

    if existing and force:
        _conn.execute("DELETE FROM hsa_receipts WHERE id = ?", (file_hash,))
        _conn.commit()

    record = {
        "id": file_hash,
        "file_path": storage_path,
        "file_name": file_name,
        "provider": provider,
        "patient_name": patient_name,
        "transaction_date": transaction_date,
        "total_amount": total_amount,
        "hsa_eligible_amount": hsa_eligible_amount,
        "category": category,
        "is_reimbursed": 0,
        "reimbursement_date": None,
        "extracted_text": extracted_text,
    }
    insert_transaction(_conn, record)
    return f"Inserted transaction with ID: {file_hash}"


@mcp.tool()
def search_ledger(
    query: str = "",
    start_date: str = "",
    end_date: str = "",
    category: str = "",
    is_reimbursed: int | None = None,
) -> str:
    results = db_search_ledger(
        _conn,
        query=query,
        start_date=start_date,
        end_date=end_date,
        category=category,
        is_reimbursed=is_reimbursed,
    )

    return json.dumps(results, default=str)


@mcp.tool()
def update_reimbursement_status(
    id: str,
    is_reimbursed: int,
    date: str | None = None,
) -> str:
    try:
        db_update_reimbursement(_conn, id, is_reimbursed, date)
        return f"Record {id} updated (reimbursed={is_reimbursed})."
    except ValueError as e:
        return str(e)
