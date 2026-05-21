import os
import shutil
import sqlite3
from datetime import date


def init_vault_dirs(base_path: str) -> None:
    for subdir in ("inbox", "storage", "archive"):
        os.makedirs(os.path.join(base_path, subdir), exist_ok=True)


def list_untracked_files(inbox_dir: str, conn: sqlite3.Connection) -> list[str]:
    cursor = conn.execute("SELECT file_name FROM hsa_receipts")
    tracked = {row[0] for row in cursor.fetchall()}

    if not os.path.isdir(inbox_dir):
        return []

    result = []
    for entry in os.listdir(inbox_dir):
        if entry.startswith("."):
            continue
        full = os.path.join(inbox_dir, entry)
        if os.path.isfile(full) and entry not in tracked:
            result.append(entry)

    return sorted(result)


def move_to_storage(
    inbox_dir: str, storage_dir: str, file_name: str, record_id: str
) -> str:
    if "/" in file_name or "\\" in file_name or file_name.startswith("."):
        raise ValueError("Invalid file name")

    src = os.path.join(inbox_dir, file_name)
    if not os.path.exists(src):
        raise FileNotFoundError(f"File not found: {src}")

    dest_name = f"{record_id}_{file_name}"
    dest = os.path.join(storage_dir, dest_name)
    shutil.move(src, dest)
    return dest


def archive_files(storage_dir: str, archive_base: str) -> list[str]:
    if not os.path.isdir(storage_dir):
        return []

    today = date.today().isoformat()
    archive_subdir = os.path.join(archive_base, "archive", today)
    os.makedirs(archive_subdir, exist_ok=True)

    moved = []
    for entry in os.listdir(storage_dir):
        full = os.path.join(storage_dir, entry)
        if os.path.isfile(full):
            shutil.move(full, os.path.join(archive_subdir, entry))
            moved.append(entry)

    return moved
