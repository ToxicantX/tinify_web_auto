import sqlite3
import os
import sys
from typing import Optional


def _get_data_dir() -> str:
    """Get writable data directory. Portable: next to exe. Dev: project root."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle → store next to exe (portable)
        return os.path.dirname(sys.executable)
    # Running from source → store in project root
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


DB_PATH = os.path.join(_get_data_dir(), "tinypng_data.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_path TEXT,
            original_name TEXT NOT NULL,
            original_size INTEGER NOT NULL,
            compressed_size INTEGER NOT NULL,
            ratio REAL NOT NULL,
            output_path TEXT,
            duration_ms INTEGER NOT NULL,
            mode TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_record(original_path: str, original_name: str, original_size: int,
               compressed_size: int, output_path: str, duration_ms: int,
               mode: str) -> int:
    ratio = round((1 - compressed_size / original_size) * 100, 1) if original_size > 0 else 0
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO history (original_path, original_name, original_size, compressed_size, "
        "ratio, output_path, duration_ms, mode) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (original_path, original_name, original_size, compressed_size, ratio,
         output_path, duration_ms, mode)
    )
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id


def get_records(page: int = 1, page_size: int = 50, keyword: Optional[str] = None,
                date_from: Optional[str] = None, date_to: Optional[str] = None):
    conn = get_connection()
    conditions = []
    params = []
    if keyword:
        conditions.append("original_name LIKE ?")
        params.append(f"%{keyword}%")
    if date_from:
        conditions.append("created_at >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("created_at <= ?")
        params.append(date_to + " 23:59:59")
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * page_size
    rows = conn.execute(
        f"SELECT * FROM history{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [page_size, offset]
    ).fetchall()
    total = conn.execute(
        f"SELECT COUNT(*) FROM history{where}", params
    ).fetchone()[0]
    conn.close()
    return [dict(r) for r in rows], total


def delete_records(ids: list[int]) -> int:
    conn = get_connection()
    placeholders = ",".join("?" * len(ids))
    cursor = conn.execute(f"DELETE FROM history WHERE id IN ({placeholders})", ids)
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return deleted


def get_total_stats():
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as count, SUM(original_size) as total_orig, "
        "SUM(compressed_size) as total_comp FROM history"
    ).fetchone()
    conn.close()
    return dict(row) if row else {"count": 0, "total_orig": 0, "total_comp": 0}
