import sqlite3

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS hsa_receipts (
    id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    provider TEXT NOT NULL,
    patient_name TEXT,
    transaction_date TEXT NOT NULL,
    total_amount REAL NOT NULL,
    hsa_eligible_amount REAL NOT NULL,
    category TEXT,
    is_reimbursed INTEGER DEFAULT 0,
    reimbursement_date TEXT,
    extracted_text TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA_SQL)
    conn.commit()
    return conn


def insert_transaction(conn: sqlite3.Connection, data: dict) -> None:
    conn.execute(
        """INSERT INTO hsa_receipts
           (id, file_path, file_name, provider, patient_name,
            transaction_date, total_amount, hsa_eligible_amount,
            category, is_reimbursed, reimbursement_date, extracted_text)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data["id"],
            data["file_path"],
            data["file_name"],
            data["provider"],
            data.get("patient_name"),
            data["transaction_date"],
            data["total_amount"],
            data["hsa_eligible_amount"],
            data.get("category"),
            data.get("is_reimbursed", 0),
            data.get("reimbursement_date"),
            data.get("extracted_text"),
        ),
    )
    conn.commit()


def get_record_by_hash(conn: sqlite3.Connection, file_hash: str) -> dict | None:
    cursor = conn.execute(
        "SELECT * FROM hsa_receipts WHERE id = ?", (file_hash,)
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def search_ledger(
    conn: sqlite3.Connection,
    query: str = "",
    start_date: str = "",
    end_date: str = "",
    category: str = "",
    is_reimbursed: int | None = None,
) -> list[dict]:
    conditions = []
    params = []

    if query:
        conditions.append(
            "(provider LIKE ? OR category LIKE ? OR extracted_text LIKE ?)"
        )
        like = f"%{query}%"
        params.extend([like, like, like])

    if start_date:
        conditions.append("transaction_date >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("transaction_date <= ?")
        params.append(end_date)

    if category:
        conditions.append("category = ?")
        params.append(category)

    if is_reimbursed is not None:
        conditions.append("is_reimbursed = ?")
        params.append(is_reimbursed)

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    cursor = conn.execute(
        f"SELECT * FROM hsa_receipts {where} ORDER BY transaction_date DESC",
        params,
    )
    return [dict(row) for row in cursor.fetchall()]


def update_reimbursement_status(
    conn: sqlite3.Connection,
    id: str,
    is_reimbursed: int,
    date: str | None = None,
) -> None:
    cursor = conn.execute(
        "SELECT id FROM hsa_receipts WHERE id = ?", (id,)
    )
    if cursor.fetchone() is None:
        raise ValueError(f"Record with id '{id}' not found")

    conn.execute(
        "UPDATE hsa_receipts SET is_reimbursed = ?, reimbursement_date = ? WHERE id = ?",
        (is_reimbursed, date, id),
    )
    conn.commit()


def get_all_records(conn: sqlite3.Connection) -> list[dict]:
    cursor = conn.execute(
        "SELECT * FROM hsa_receipts ORDER BY transaction_date DESC"
    )
    return [dict(row) for row in cursor.fetchall()]


def get_stats(conn: sqlite3.Connection) -> dict:
    cursor = conn.execute(
        """SELECT
           COUNT(*) as total_records,
           COALESCE(SUM(CASE WHEN is_reimbursed = 0 THEN hsa_eligible_amount ELSE 0 END), 0) as unreimbursed_total,
           COALESCE(SUM(hsa_eligible_amount), 0) as total_hsa_eligible
           FROM hsa_receipts"""
    )
    return dict(cursor.fetchone())
