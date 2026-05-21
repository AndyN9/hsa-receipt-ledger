import os
import sqlite3
import pytest


@pytest.fixture
def tmp_db_path(tmp_path):
    return os.path.join(tmp_path, "test.db")


@pytest.fixture
def empty_db(tmp_db_path):
    from hsa_ledger.database import init_db

    conn = init_db(tmp_db_path)
    yield conn
    conn.close()


@pytest.fixture
def sample_record():
    return {
        "id": "abc123def456",
        "file_path": "storage/abc123def456_receipt.pdf",
        "file_name": "receipt.pdf",
        "provider": "Quest Diagnostics",
        "patient_name": "Self",
        "transaction_date": "2024-03-15",
        "total_amount": 187.50,
        "hsa_eligible_amount": 187.50,
        "category": "Lab Work",
        "is_reimbursed": 0,
        "reimbursement_date": None,
        "extracted_text": "Quest Diagnostics\nTotal: $187.50",
    }


@pytest.fixture
def populated_db(empty_db, sample_record):
    from hsa_ledger.database import insert_transaction

    insert_transaction(empty_db, sample_record)
    return empty_db
