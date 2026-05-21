import os
import sqlite3
import pytest


class TestInitDB:
    def test_creates_db_file(self, tmp_db_path):
        from hsa_ledger.database import init_db

        conn = init_db(tmp_db_path)
        assert os.path.exists(tmp_db_path)
        conn.close()

    def test_creates_hsa_receipts_table(self, empty_db):
        cursor = empty_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='hsa_receipts'"
        )
        assert cursor.fetchone() is not None

    def test_schema_has_all_columns(self, empty_db):
        cursor = empty_db.execute("PRAGMA table_info(hsa_receipts)")
        columns = {row[1] for row in cursor.fetchall()}
        expected = {
            "id", "file_path", "file_name", "provider", "patient_name",
            "transaction_date", "total_amount", "hsa_eligible_amount",
            "category", "is_reimbursed", "reimbursement_date",
            "extracted_text", "created_at",
        }
        assert columns == expected

    def test_is_idempotent(self, tmp_db_path):
        from hsa_ledger.database import init_db

        conn1 = init_db(tmp_db_path)
        conn2 = init_db(tmp_db_path)
        cursor = conn2.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='hsa_receipts'"
        )
        assert cursor.fetchone()[0] == 1
        conn1.close()
        conn2.close()


class TestInsertTransaction:
    def test_inserts_record(self, empty_db, sample_record):
        from hsa_ledger.database import insert_transaction

        insert_transaction(empty_db, sample_record)
        cursor = empty_db.execute("SELECT COUNT(*) FROM hsa_receipts")
        assert cursor.fetchone()[0] == 1

    def test_raises_on_duplicate_id(self, empty_db, sample_record):
        from hsa_ledger.database import insert_transaction

        insert_transaction(empty_db, sample_record)
        with pytest.raises(sqlite3.IntegrityError):
            insert_transaction(empty_db, sample_record)


class TestGetRecordByHash:
    def test_returns_record_when_found(self, populated_db):
        from hsa_ledger.database import get_record_by_hash

        record = get_record_by_hash(populated_db, "abc123def456")
        assert record is not None
        assert record["provider"] == "Quest Diagnostics"

    def test_returns_none_when_not_found(self, empty_db):
        from hsa_ledger.database import get_record_by_hash

        record = get_record_by_hash(empty_db, "nonexistent")
        assert record is None


class TestSearchLedger:
    def test_returns_all_without_filters(self, populated_db):
        from hsa_ledger.database import search_ledger

        results = search_ledger(populated_db)
        assert len(results) >= 1

    def test_filters_by_provider(self, populated_db):
        from hsa_ledger.database import search_ledger

        results = search_ledger(populated_db, query="Quest")
        assert len(results) == 1

    def test_filters_by_category(self, populated_db):
        from hsa_ledger.database import search_ledger

        results = search_ledger(populated_db, category="Lab Work")
        assert len(results) == 1

    def test_filters_by_date_range(self, populated_db):
        from hsa_ledger.database import search_ledger

        results = search_ledger(
            populated_db, start_date="2024-01-01", end_date="2024-12-31"
        )
        assert len(results) == 1

    def test_filters_by_reimbursement_status(self, populated_db):
        from hsa_ledger.database import search_ledger

        results = search_ledger(populated_db, is_reimbursed=0)
        assert len(results) == 1
        results = search_ledger(populated_db, is_reimbursed=1)
        assert len(results) == 0

    def test_combines_filters(self, populated_db):
        from hsa_ledger.database import search_ledger

        results = search_ledger(
            populated_db,
            category="Lab Work",
            is_reimbursed=0,
        )
        assert len(results) == 1

    def test_returns_empty_when_no_match(self, populated_db):
        from hsa_ledger.database import search_ledger

        results = search_ledger(populated_db, query="NonexistentProvider")
        assert len(results) == 0


class TestUpdateReimbursementStatus:
    def test_updates_status_and_date(self, populated_db):
        from hsa_ledger.database import update_reimbursement_status

        update_reimbursement_status(
            populated_db, "abc123def456", is_reimbursed=1, date="2025-01-15"
        )
        cursor = populated_db.execute(
            "SELECT is_reimbursed, reimbursement_date FROM hsa_receipts WHERE id = ?",
            ("abc123def456",),
        )
        row = cursor.fetchone()
        assert row[0] == 1
        assert row[1] == "2025-01-15"

    def test_can_unset_reimbursement(self, populated_db):
        from hsa_ledger.database import update_reimbursement_status

        update_reimbursement_status(
            populated_db, "abc123def456", is_reimbursed=1, date="2025-01-15"
        )
        update_reimbursement_status(
            populated_db, "abc123def456", is_reimbursed=0, date=None
        )
        cursor = populated_db.execute(
            "SELECT is_reimbursed, reimbursement_date FROM hsa_receipts WHERE id = ?",
            ("abc123def456",),
        )
        row = cursor.fetchone()
        assert row[0] == 0
        assert row[1] is None

    def test_raises_on_nonexistent_id(self, empty_db):
        from hsa_ledger.database import update_reimbursement_status

        with pytest.raises(ValueError, match="not found"):
            update_reimbursement_status(
                empty_db, "nonexistent", is_reimbursed=1, date="2025-01-15"
            )


class TestGetAllRecords:
    def test_returns_all_records(self, populated_db):
        from hsa_ledger.database import get_all_records

        records = get_all_records(populated_db)
        assert len(records) == 1

    def test_returns_empty_list_when_no_records(self, empty_db):
        from hsa_ledger.database import get_all_records

        records = get_all_records(empty_db)
        assert records == []


class TestGetStats:
    def test_returns_correct_stats(self, populated_db):
        from hsa_ledger.database import get_stats

        stats = get_stats(populated_db)
        assert stats["total_records"] == 1
        assert stats["unreimbursed_total"] == 187.50
        assert stats["total_hsa_eligible"] == 187.50
