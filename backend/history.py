from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.config import DB_PATH, ensure_data_dir


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class HistoryStore:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        ensure_data_dir()
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    input_dir TEXT NOT NULL,
                    output_dir TEXT NOT NULL,
                    total INTEGER NOT NULL DEFAULT 0,
                    success_count INTEGER NOT NULL DEFAULT 0,
                    failed_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'running'
                );
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id INTEGER NOT NULL,
                    source_path TEXT NOT NULL,
                    output_name TEXT,
                    status TEXT NOT NULL,
                    error_msg TEXT,
                    finished_at TEXT,
                    FOREIGN KEY (batch_id) REFERENCES batches(id)
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )

    def get_setting(self, key: str, default: str = "") -> str:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    def create_batch(self, input_dir: str, output_dir: str, total: int) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO batches(started_at, input_dir, output_dir, total, status)
                VALUES (?, ?, ?, ?, 'running')
                """,
                (_utc_now(), input_dir, output_dir, total),
            )
            return int(cur.lastrowid)

    def finish_batch(
        self,
        batch_id: int,
        success_count: int,
        failed_count: int,
        status: str = "completed",
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE batches
                SET finished_at = ?, success_count = ?, failed_count = ?, status = ?
                WHERE id = ?
                """,
                (_utc_now(), success_count, failed_count, status, batch_id),
            )

    def add_item(
        self,
        batch_id: int,
        source_path: str,
        output_name: str | None,
        status: str,
        error_msg: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO items(batch_id, source_path, output_name, status, error_msg, finished_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (batch_id, source_path, output_name, status, error_msg, _utc_now()),
            )

    def list_batches(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM batches
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_batch_items(self, batch_id: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM items
                WHERE batch_id = ?
                ORDER BY id ASC
                """,
                (batch_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def mark_interrupted_batches(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE batches
                SET status = 'interrupted', finished_at = ?
                WHERE status = 'running'
                """,
                (_utc_now(),),
            )
