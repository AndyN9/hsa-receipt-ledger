import os
import sys
import csv
import click

from hsa_ledger.database import init_db, get_all_records, get_stats
from hsa_ledger.vault import init_vault_dirs, archive_files


@click.group()
def cli():
    pass


def _get_default_vault():
    return os.path.join(os.getcwd(), "hsa_vault")


def _get_default_db():
    return os.path.join(os.getcwd(), "hsa_ledger.db")


@cli.command()
@click.option("--vault", default=None, help="Vault directory path")
@click.option("--db", default=None, help="Database file path")
def init(vault, db):
    vault = vault or _get_default_vault()
    db = db or _get_default_db()
    init_vault_dirs(vault)
    conn = init_db(db)
    conn.close()
    click.echo(f"Initialized vault at {vault}")
    click.echo(f"Initialized database at {db}")


@cli.command()
@click.option("--vault", default=None, help="Vault directory path")
@click.option("--db", default=None, help="Database file path")
def status(vault, db):
    vault = vault or _get_default_vault()
    db = db or _get_default_db()
    conn = init_db(db)
    stats = get_stats(conn)
    conn.close()

    inbox = os.path.join(vault, "inbox")
    inbox_count = len([
        f for f in os.listdir(inbox)
        if os.path.isfile(os.path.join(inbox, f)) and not f.startswith(".")
    ]) if os.path.isdir(inbox) else 0

    click.echo(f"Total records:       {stats['total_records']}")
    click.echo(f"Unreimbursed total:  ${stats['unreimbursed_total']:.2f}")
    click.echo(f"Total HSA eligible:  ${stats['total_hsa_eligible']:.2f}")
    click.echo(f"Inbox file count:    {inbox_count}")


@cli.command()
@click.option("--dry-run", is_flag=True, help="Preview what would be deleted")
@click.option("--force", is_flag=True, help="Execute the clear operation")
@click.option("--vault", default=None, help="Vault directory path")
@click.option("--db", default=None, help="Database file path")
def clear(dry_run, force, vault, db):
    if not dry_run and not force:
        click.echo("Use --dry-run to preview or --force to execute.")
        sys.exit(1)

    vault = vault or _get_default_vault()
    db = db or _get_default_db()
    storage_dir = os.path.join(vault, "storage")
    conn = init_db(db)
    records = get_all_records(conn)
    conn.close()

    storage_files = [
        f for f in os.listdir(storage_dir)
        if os.path.isfile(os.path.join(storage_dir, f))
    ] if os.path.isdir(storage_dir) else []

    if dry_run:
        click.echo(f"Would delete {len(records)} record(s) from database")
        click.echo(f"Would archive {len(storage_files)} file(s) from storage")
        return

    if force:
        conn = init_db(db)
        cursor = conn.execute("DELETE FROM hsa_receipts")
        conn.commit()
        count = cursor.rowcount
        conn.close()

        archived = archive_files(storage_dir, vault)
        click.echo(f"Deleted {count} record(s) from database")
        click.echo(f"Archived {len(archived)} file(s) to archive/")


@cli.command()
@click.option("--csv", "csv_path", required=True, help="Output CSV file path")
@click.option("--vault", default=None, help="Vault directory path")
@click.option("--db", default=None, help="Database file path")
def export(csv_path, vault, db):
    vault = vault or _get_default_vault()
    db = db or _get_default_db()
    conn = init_db(db)
    records = get_all_records(conn)
    conn.close()

    if not records:
        click.echo("No records to export.")
        return

    fieldnames = [
        "id", "file_path", "file_name", "provider", "patient_name",
        "transaction_date", "total_amount", "hsa_eligible_amount",
        "category", "is_reimbursed", "reimbursement_date",
        "extracted_text", "created_at",
    ]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    click.echo(f"Exported {len(records)} record(s) to {csv_path}")


@cli.command()
@click.option("--vault", default=None, help="Vault directory path")
@click.option("--db", default=None, help="Database file path")
def ui(vault, db):
    import streamlit.web.cli as st_cli

    vault = vault or _get_default_vault()
    db = db or _get_default_db()
    os.environ["HSA_LEDGER_VAULT"] = vault
    os.environ["HSA_LEDGER_DB"] = db

    sys.argv = [
        "streamlit", "run",
        os.path.join(os.path.dirname(__file__), "ui.py"),
    ]
    st_cli.main()


def run_mcp():
    from hsa_ledger.server import mcp, init_server

    vault = _get_default_vault()
    db = _get_default_db()
    init_server(vault, db)
    mcp.run()


@cli.command()
def mcp():
    run_mcp()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "mcp":
        run_mcp()
    else:
        cli()


if __name__ == "__main__":
    main()
