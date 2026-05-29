"""
Run Logger
==========
Persists every task execution and payout event to SQLite.
Provides summary + recent-run queries used by the CLI and scorer.
"""

import sqlite3
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "data" / "miner.db"


@dataclass
class RunRecord:
    task_id: int
    task_name: str
    status: str            # "success" | "failure" | "skipped"
    earnings_usd: float = 0.0
    notes: str = ""
    timestamp: Optional[float] = None
    id: Optional[int] = None


class RunLogger:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id      INTEGER NOT NULL,
                    task_name    TEXT    NOT NULL,
                    status       TEXT    NOT NULL,
                    earnings_usd REAL    DEFAULT 0.0,
                    notes        TEXT    DEFAULT '',
                    timestamp    REAL    NOT NULL
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS payouts (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name  TEXT  NOT NULL,
                    amount_usd REAL  NOT NULL,
                    method     TEXT  DEFAULT '',
                    timestamp  REAL  NOT NULL,
                    notes      TEXT  DEFAULT ''
                )
            """)
            c.commit()

    def log(self, record: RunRecord):
        ts = record.timestamp or time.time()
        with self._conn() as c:
            c.execute("""
                INSERT INTO runs
                    (task_id, task_name, status, earnings_usd, notes, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                record.task_id, record.task_name, record.status,
                record.earnings_usd, record.notes, ts,
            ))
            c.commit()

    def log_payout(
        self,
        task_name: str,
        amount_usd: float,
        method: str = "",
        notes: str = "",
    ):
        with self._conn() as c:
            c.execute("""
                INSERT INTO payouts (task_name, amount_usd, method, timestamp, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (task_name, amount_usd, method, time.time(), notes))
            c.commit()

    def recent(self, limit: int = 20) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("""
                SELECT task_name, status, earnings_usd, notes, timestamp
                FROM runs ORDER BY timestamp DESC LIMIT ?
            """, (limit,)).fetchall()
        return [dict(r) for r in rows]

    def summary(self, days: int = 30) -> dict:
        since = time.time() - (days * 86400)
        with self._conn() as c:
            run_rows = c.execute("""
                SELECT task_name, status,
                       COUNT(*) AS cnt,
                       COALESCE(SUM(earnings_usd), 0) AS total
                FROM runs
                WHERE timestamp >= ?
                GROUP BY task_name, status
            """, (since,)).fetchall()

            payout_total = c.execute("""
                SELECT COALESCE(SUM(amount_usd), 0)
                FROM payouts WHERE timestamp >= ?
            """, (since,)).fetchone()[0]

        tasks: dict = {}
        for row in run_rows:
            name = row["task_name"]
            if name not in tasks:
                tasks[name] = {
                    "success": 0, "failure": 0,
                    "skipped": 0, "earnings_usd": 0.0,
                }
            tasks[name][row["status"]] = row["cnt"]
            tasks[name]["earnings_usd"] += row["total"]

        return {
            "period_days": days,
            "tasks": tasks,
            "payout_total_usd": payout_total,
        }

    def task_history(self, task_name: str, limit: int = 50) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("""
                SELECT status, earnings_usd, notes, timestamp
                FROM runs WHERE task_name = ?
                ORDER BY timestamp DESC LIMIT ?
            """, (task_name, limit)).fetchall()
        return [dict(r) for r in rows]
