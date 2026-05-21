import os
import json
import hashlib
import pytest
from hsa_ledger.database import insert_transaction


@pytest.fixture
def vault_env(tmp_path):
    from hsa_ledger.vault import init_vault_dirs

    init_vault_dirs(tmp_path)
    inbox = os.path.join(tmp_path, "inbox")
    storage = os.path.join(tmp_path, "storage")
    db_path = os.path.join(tmp_path, "test.db")
    return tmp_path, inbox, storage, db_path


@pytest.fixture
def fresh_server(vault_env):
    from hsa_ledger import server

    tmp_path, inbox, storage, db_path = vault_env
    server.init_server(str(tmp_path), db_path)
    yield server
    server._conn.close()


class TestListUntrackedFiles:
    def test_returns_untracked_files(self, fresh_server, vault_env):
        _, inbox, _, _ = vault_env
        for fname in ("new1.pdf", "new2.png"):
            with open(os.path.join(inbox, fname), "w") as f:
                f.write("data")

        result = fresh_server.list_untracked_files()
        assert "new1.pdf" in result
        assert "new2.png" in result

    def test_excludes_tracked(self, fresh_server, vault_env, sample_record):
        _, inbox, _, _ = vault_env
        fname = "tracked.pdf"
        with open(os.path.join(inbox, fname), "w") as f:
            f.write("data")
        rec = dict(sample_record)
        rec["file_name"] = fname
        rec["file_path"] = f"storage/{fname}"
        insert_transaction(fresh_server._conn, rec)

        result = fresh_server.list_untracked_files()
        assert fname not in result


class TestExtractFileText:
    def test_extracts_pdf_text(self, mocker, fresh_server, vault_env):
        _, inbox, _, _ = vault_env
        fname = "receipt.pdf"
        with open(os.path.join(inbox, fname), "w") as f:
            f.write("dummy")

        mock_reader = mocker.patch("pypdf.PdfReader")
        mock_page = mocker.MagicMock()
        mock_page.extract_text.return_value = "Lab Work $150"
        mock_reader.return_value.pages = [mock_page]

        result = fresh_server.extract_file_text(fname)
        assert "Lab Work" in result

    def test_returns_error_on_missing_file(self, fresh_server):
        result = fresh_server.extract_file_text("nonexistent.pdf")
        assert "error" in result.lower() or "not found" in result.lower()

    def test_rejects_path_traversal(self, fresh_server):
        result = fresh_server.extract_file_text("../../etc/passwd")
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_returns_error_on_unsupported_format(self, fresh_server, vault_env):
        _, inbox, _, _ = vault_env
        fname = "receipt.txt"
        with open(os.path.join(inbox, fname), "w") as f:
            f.write("not a receipt")

        result = fresh_server.extract_file_text(fname)
        assert "unsupported" in result.lower()


class TestInsertHSATransaction:
    def test_inserts_and_returns_id(self, fresh_server, vault_env):
        _, inbox, _, _ = vault_env
        fname = "receipt.pdf"
        fpath = os.path.join(inbox, fname)
        content = b"test content"
        with open(fpath, "wb") as f:
            f.write(content)

        file_hash = hashlib.sha256(content).hexdigest()

        result = fresh_server.insert_hsa_transaction(
            file_name=fname,
            provider="Test Provider",
            patient_name="Self",
            transaction_date="2024-01-15",
            total_amount=100.00,
            hsa_eligible_amount=100.00,
            category="Lab Work",
        )

        assert file_hash in result
        assert not os.path.exists(fpath)

    def test_detects_duplicate_hash(self, fresh_server, vault_env):
        _, inbox, _, _ = vault_env
        fname = "dup.pdf"
        content = b"duplicate content"
        with open(os.path.join(inbox, fname), "wb") as f:
            f.write(content)

        fresh_server.insert_hsa_transaction(
            file_name=fname,
            provider="First",
            patient_name="Self",
            transaction_date="2024-01-15",
            total_amount=50.00,
            hsa_eligible_amount=50.00,
            category="Lab Work",
        )

        with open(os.path.join(inbox, fname), "wb") as f:
            f.write(content)

        result = fresh_server.insert_hsa_transaction(
            file_name=fname,
            provider="Second",
            patient_name="Self",
            transaction_date="2024-01-15",
            total_amount=50.00,
            hsa_eligible_amount=50.00,
            category="Lab Work",
        )

        assert "duplicate" in result.lower() or "conflict" in result.lower()

    def test_force_overrides_duplicate(self, fresh_server, vault_env):
        _, inbox, _, _ = vault_env
        fname = "forced.pdf"
        content = b"force content"
        with open(os.path.join(inbox, fname), "wb") as f:
            f.write(content)

        fresh_server.insert_hsa_transaction(
            file_name=fname,
            provider="First",
            patient_name="Self",
            transaction_date="2024-01-15",
            total_amount=50.00,
            hsa_eligible_amount=50.00,
            category="Lab Work",
        )

        with open(os.path.join(inbox, fname), "wb") as f:
            f.write(content)

        result = fresh_server.insert_hsa_transaction(
            file_name=fname,
            provider="Override",
            patient_name="Self",
            transaction_date="2024-01-15",
            total_amount=75.00,
            hsa_eligible_amount=75.00,
            category="Lab Work",
            force=True,
        )

        assert "Inserted" in result

    def test_returns_error_for_missing_file(self, fresh_server, vault_env):
        _, inbox, _, _ = vault_env
        result = fresh_server.insert_hsa_transaction(
            file_name="nonexistent.pdf",
            provider="Test",
            transaction_date="2024-01-15",
            total_amount=50.00,
            hsa_eligible_amount=50.00,
        )
        assert "no such file" in result.lower() or "not found" in result.lower()

    def test_validates_required_fields(self, fresh_server):
        result = fresh_server.insert_hsa_transaction(
            file_name="test.pdf",
            provider="",
            transaction_date=None,
            total_amount=None,
            hsa_eligible_amount=None,
        )
        assert "missing" in result.lower()

    def test_rejects_path_traversal(self, fresh_server, vault_env):
        _, inbox, _, _ = vault_env
        result = fresh_server.insert_hsa_transaction(
            file_name="../../etc/passwd",
            provider="Test",
            transaction_date="2024-01-15",
            total_amount=50.00,
            hsa_eligible_amount=50.00,
        )
        assert "invalid" in result.lower()


class TestSearchLedger:
    def test_returns_results(self, fresh_server, sample_record):
        rec = dict(sample_record)
        rec["file_path"] = "storage/abc123_receipt.pdf"
        insert_transaction(fresh_server._conn, rec)

        results = fresh_server.search_ledger(query="Quest")
        parsed = json.loads(results)
        assert len(parsed) == 1
        assert parsed[0]["provider"] == "Quest Diagnostics"


class TestUpdateReimbursementStatus:
    def test_updates_and_returns_success(self, fresh_server, sample_record):
        rec = dict(sample_record)
        rec["file_path"] = "storage/abc123_receipt.pdf"
        insert_transaction(fresh_server._conn, rec)

        result = fresh_server.update_reimbursement_status(
            id="abc123def456", is_reimbursed=1, date="2025-01-15"
        )
        assert "updated" in result.lower()

    def test_returns_error_for_nonexistent_id(self, fresh_server):
        result = fresh_server.update_reimbursement_status(
            id="nonexistent", is_reimbursed=1, date="2025-01-15"
        )
        assert "not found" in result.lower()
