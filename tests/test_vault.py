import os
import pytest


class TestInitVaultDirs:
    def test_creates_inbox_storage_archive(self, tmp_path):
        from hsa_ledger.vault import init_vault_dirs

        init_vault_dirs(tmp_path)

        assert os.path.isdir(os.path.join(tmp_path, "inbox"))
        assert os.path.isdir(os.path.join(tmp_path, "storage"))
        assert os.path.isdir(os.path.join(tmp_path, "archive"))

    def test_is_idempotent(self, tmp_path):
        from hsa_ledger.vault import init_vault_dirs

        init_vault_dirs(tmp_path)
        init_vault_dirs(tmp_path)

        assert os.path.isdir(os.path.join(tmp_path, "inbox"))


class TestListUntrackedFiles:
    def test_returns_all_files_when_db_empty(self, tmp_path, empty_db):
        from hsa_ledger.vault import init_vault_dirs, list_untracked_files

        init_vault_dirs(tmp_path)
        inbox = os.path.join(tmp_path, "inbox")
        os.makedirs(inbox, exist_ok=True)

        for fname in ("receipt1.pdf", "receipt2.png"):
            with open(os.path.join(inbox, fname), "w") as f:
                f.write("test")

        files = list_untracked_files(inbox, empty_db)
        assert sorted(files) == ["receipt1.pdf", "receipt2.png"]

    def test_excludes_tracked_files(self, tmp_path, empty_db, sample_record):
        from hsa_ledger.vault import init_vault_dirs, list_untracked_files
        from hsa_ledger.database import insert_transaction

        init_vault_dirs(tmp_path)
        inbox = os.path.join(tmp_path, "inbox")
        os.makedirs(inbox, exist_ok=True)

        for fname in ("tracked.pdf", "untracked.png"):
            with open(os.path.join(inbox, fname), "w") as f:
                f.write("test")

        record = dict(sample_record)
        record["file_name"] = "tracked.pdf"
        insert_transaction(empty_db, record)

        files = list_untracked_files(inbox, empty_db)
        assert "tracked.pdf" not in files
        assert "untracked.png" in files

    def test_returns_empty_when_all_tracked(self, tmp_path, empty_db, sample_record):
        from hsa_ledger.vault import init_vault_dirs, list_untracked_files
        from hsa_ledger.database import insert_transaction

        init_vault_dirs(tmp_path)
        inbox = os.path.join(tmp_path, "inbox")
        os.makedirs(inbox, exist_ok=True)

        record = dict(sample_record)
        record["file_name"] = "receipt.pdf"
        insert_transaction(empty_db, record)

        with open(os.path.join(inbox, "receipt.pdf"), "w") as f:
            f.write("test")

        files = list_untracked_files(inbox, empty_db)
        assert files == []

    def test_returns_empty_when_inbox_empty(self, tmp_path, empty_db):
        from hsa_ledger.vault import init_vault_dirs, list_untracked_files

        init_vault_dirs(tmp_path)
        inbox = os.path.join(tmp_path, "inbox")
        os.makedirs(inbox, exist_ok=True)

        files = list_untracked_files(inbox, empty_db)
        assert files == []

    def test_ignores_dotfiles(self, tmp_path, empty_db):
        from hsa_ledger.vault import init_vault_dirs, list_untracked_files

        init_vault_dirs(tmp_path)
        inbox = os.path.join(tmp_path, "inbox")
        os.makedirs(inbox, exist_ok=True)

        with open(os.path.join(inbox, ".hidden"), "w") as f:
            f.write("test")
        with open(os.path.join(inbox, "receipt.pdf"), "w") as f:
            f.write("test")

        files = list_untracked_files(inbox, empty_db)
        assert ".hidden" not in files
        assert "receipt.pdf" in files


class TestMoveToStorage:
    def test_moves_file_from_inbox_to_storage(self, tmp_path):
        from hsa_ledger.vault import init_vault_dirs, move_to_storage

        init_vault_dirs(tmp_path)
        inbox = os.path.join(tmp_path, "inbox")
        storage = os.path.join(tmp_path, "storage")

        src = os.path.join(inbox, "receipt.pdf")
        with open(src, "w") as f:
            f.write("content")

        dest_path = move_to_storage(
            inbox, storage, "receipt.pdf", "abc123"
        )

        assert not os.path.exists(src)
        assert os.path.exists(dest_path)
        assert "abc123" in dest_path
        assert "receipt.pdf" in dest_path

    def test_raises_on_missing_file(self, tmp_path):
        from hsa_ledger.vault import init_vault_dirs, move_to_storage

        init_vault_dirs(tmp_path)
        inbox = os.path.join(tmp_path, "inbox")
        storage = os.path.join(tmp_path, "storage")

        with pytest.raises(FileNotFoundError):
            move_to_storage(inbox, storage, "nonexistent.pdf", "abc123")


class TestArchiveFiles:
    def test_moves_file_to_dated_subdirectory(self, tmp_path):
        from hsa_ledger.vault import init_vault_dirs, archive_files

        init_vault_dirs(tmp_path)
        storage = os.path.join(tmp_path, "storage")

        with open(os.path.join(storage, "file1.pdf"), "w") as f:
            f.write("data")
        with open(os.path.join(storage, "file2.pdf"), "w") as f:
            f.write("data")

        archived = archive_files(storage, tmp_path)

        assert len(archived) == 2

        for fname in ("file1.pdf", "file2.pdf"):
            assert not os.path.exists(os.path.join(storage, fname))


class TestPathTraversalPrevention:
    def test_move_to_storage_rejects_relative_path_escape(self, tmp_path):
        from hsa_ledger.vault import init_vault_dirs, move_to_storage

        init_vault_dirs(tmp_path)

        with pytest.raises(ValueError, match="Invalid file name"):
            move_to_storage(
                os.path.join(tmp_path, "inbox"),
                os.path.join(tmp_path, "storage"),
                "../../etc/passwd",
                "abc123",
            )
