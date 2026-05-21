import os
import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cli_vault(tmp_path):
    vault = os.path.join(tmp_path, "hsa_vault")
    db = os.path.join(tmp_path, "hsa_ledger.db")
    return vault, db


class TestInit:
    def test_creates_vault_dirs_and_db(self, runner, cli_vault):
        from hsa_ledger.__main__ import cli

        vault, db = cli_vault
        result = runner.invoke(cli, ["init", "--vault", vault, "--db", db])
        assert result.exit_code == 0
        assert os.path.isdir(os.path.join(vault, "inbox"))
        assert os.path.isdir(os.path.join(vault, "storage"))
        assert os.path.isdir(os.path.join(vault, "archive"))
        assert os.path.exists(db)

    def test_is_idempotent(self, runner, cli_vault):
        from hsa_ledger.__main__ import cli

        vault, db = cli_vault
        runner.invoke(cli, ["init", "--vault", vault, "--db", db])
        result = runner.invoke(cli, ["init", "--vault", vault, "--db", db])
        assert result.exit_code == 0


class TestStatus:
    def test_shows_zero_when_empty(self, runner, cli_vault):
        from hsa_ledger.__main__ import cli

        vault, db = cli_vault
        runner.invoke(cli, ["init", "--vault", vault, "--db", db])
        result = runner.invoke(cli, ["status", "--vault", vault, "--db", db])
        assert result.exit_code == 0
        assert "0" in result.output

    def test_shows_counts_with_data(self, runner, cli_vault, sample_record):
        from hsa_ledger.__main__ import cli
        from hsa_ledger.database import init_db, insert_transaction

        vault, db = cli_vault
        runner.invoke(cli, ["init", "--vault", vault, "--db", db])

        conn = init_db(db)
        rec = dict(sample_record)
        rec["file_path"] = "storage/abc123_receipt.pdf"
        insert_transaction(conn, rec)
        conn.close()

        result = runner.invoke(cli, ["status", "--vault", vault, "--db", db])
        assert "1" in result.output
        assert "187.50" in result.output


class TestClear:
    def test_requires_flag(self, runner, cli_vault):
        from hsa_ledger.__main__ import cli

        vault, db = cli_vault
        runner.invoke(cli, ["init", "--vault", vault, "--db", db])
        result = runner.invoke(
            cli, ["clear", "--vault", vault, "--db", db]
        )
        assert result.exit_code != 0

    def test_dry_run_shows_preview(self, runner, cli_vault, sample_record):
        from hsa_ledger.__main__ import cli
        from hsa_ledger.database import init_db, insert_transaction, get_all_records

        vault, db = cli_vault
        runner.invoke(cli, ["init", "--vault", vault, "--db", db])

        conn = init_db(db)
        rec = dict(sample_record)
        rec["file_path"] = "storage/abc123_receipt.pdf"
        insert_transaction(conn, rec)
        conn.close()

        result = runner.invoke(
            cli, ["clear", "--dry-run", "--vault", vault, "--db", db]
        )
        assert result.exit_code == 0
        assert "1 record" in result.output

        conn = init_db(db)
        assert len(get_all_records(conn)) == 1
        conn.close()

    def test_force_clears_records(self, runner, cli_vault, sample_record):
        from hsa_ledger.__main__ import cli
        from hsa_ledger.database import init_db, insert_transaction, get_all_records

        vault, db = cli_vault
        runner.invoke(cli, ["init", "--vault", vault, "--db", db])

        conn = init_db(db)
        rec = dict(sample_record)
        rec["file_path"] = "storage/abc123_receipt.pdf"
        insert_transaction(conn, rec)
        conn.close()

        result = runner.invoke(
            cli, ["clear", "--force", "--vault", vault, "--db", db]
        )
        assert result.exit_code == 0

        conn = init_db(db)
        assert get_all_records(conn) == []
        conn.close()


class TestExport:
    def test_exports_empty(self, runner, cli_vault):
        from hsa_ledger.__main__ import cli

        vault, db = cli_vault
        runner.invoke(cli, ["init", "--vault", vault, "--db", db])

        out_csv = os.path.join(os.path.dirname(vault), "export.csv")
        result = runner.invoke(
            cli, ["export", "--csv", out_csv, "--vault", vault, "--db", db]
        )
        assert result.exit_code == 0
        assert "No records" in result.output

    def test_exports_csv(self, runner, cli_vault, sample_record):
        from hsa_ledger.__main__ import cli
        from hsa_ledger.database import init_db, insert_transaction

        vault, db = cli_vault
        runner.invoke(cli, ["init", "--vault", vault, "--db", db])

        conn = init_db(db)
        rec = dict(sample_record)
        rec["file_path"] = "storage/abc123_receipt.pdf"
        insert_transaction(conn, rec)
        conn.close()

        out_csv = os.path.join(os.path.dirname(vault), "export.csv")
        result = runner.invoke(
            cli, ["export", "--csv", out_csv, "--vault", vault, "--db", db]
        )
        assert result.exit_code == 0
        assert os.path.exists(out_csv)
        with open(out_csv) as f:
            content = f.read()
        assert "provider" in content
        assert "Quest Diagnostics" in content
