"""
Task State Store
================
Stores persistent task runtime state.
"""

import sqlite3
import json
import time
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "miner.db"


class TaskStateStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS task_state (
                    task_name TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            c.commit()

    def get(self, task_name: str) -> dict:
        with self._conn() as c:
            row = c.execute(
                "SELECT state_json FROM task_state WHERE task_name = ?",
                (task_name,)
            ).fetchone()

        if not row:
            return {}

        return json.loads(row["state_json"])

    def set(self, task_name: str, state: dict):
        with self._conn() as c:
            c.execute("""
                INSERT INTO task_state (task_name, state_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(task_name) DO UPDATE SET
                    state_json = excluded.state_json,
                    updated_at = excluded.updated_at
            """, (
                task_name,
                json.dumps(state),
                time.time(),
            ))
            c.commit()
