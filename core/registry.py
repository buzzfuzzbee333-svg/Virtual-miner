"""
Task Registry
=============
SQLite-backed store for all automation tasks.
Each task has a name, platform, cooldown, and a flow (list of steps).
"""

import sqlite3
import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "data" / "miner.db"


@dataclass
class Task:
    name: str
    platform: str          # "web" | "android"
    cooldown_seconds: int
    flow: dict             # {"steps": [...]}
    enabled: bool = True
    id: Optional[int] = None
    last_run: Optional[float] = None
    url: Optional[str] = None
    description: str = ""
    tags: list = field(default_factory=list)


class TaskRegistry:
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
                CREATE TABLE IF NOT EXISTS tasks (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    name             TEXT    UNIQUE NOT NULL,
                    platform         TEXT    NOT NULL,
                    cooldown_seconds INTEGER NOT NULL,
                    flow_json        TEXT    NOT NULL,
                    enabled          INTEGER DEFAULT 1,
                    last_run         REAL,
                    url              TEXT,
                    description      TEXT    DEFAULT '',
                    tags             TEXT    DEFAULT '[]'
                )
            """)
            c.commit()

    def _row_to_task(self, row) -> Task:
        return Task(
            id=row["id"],
            name=row["name"],
            platform=row["platform"],
            cooldown_seconds=row["cooldown_seconds"],
            flow=json.loads(row["flow_json"]),
            enabled=bool(row["enabled"]),
            last_run=row["last_run"],
            url=row["url"],
            description=row["description"] or "",
            tags=json.loads(row["tags"] or "[]"),
        )

    def register(self, task: Task) -> int:
        with self._conn() as c:
            cur = c.execute("""
                INSERT INTO tasks
                    (name, platform, cooldown_seconds, flow_json, enabled,
                     last_run, url, description, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    platform         = excluded.platform,
                    cooldown_seconds = excluded.cooldown_seconds,
                    flow_json        = excluded.flow_json,
                    enabled          = excluded.enabled,
                    url              = excluded.url,
                    description      = excluded.description,
                    tags             = excluded.tags
            """, (
                task.name, task.platform, task.cooldown_seconds,
                json.dumps(task.flow), int(task.enabled),
                task.last_run, task.url, task.description,
                json.dumps(task.tags),
            ))
            c.commit()
            return cur.lastrowid

    def get_all(self) -> list[Task]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM tasks ORDER BY name"
            ).fetchall()
        return [self._row_to_task(r) for r in rows]

    def get_by_name(self, name: str) -> Optional[Task]:
        with self._conn() as c:
            row = c.execute(
                "SELECT * FROM tasks WHERE name = ?", (name,)
            ).fetchone()
        return self._row_to_task(row) if row else None

    def get_due(self) -> list[Task]:
        now = time.time()
        with self._conn() as c:
            rows = c.execute("""
                SELECT * FROM tasks
                WHERE enabled = 1
                  AND (last_run IS NULL OR last_run + cooldown_seconds <= ?)
                ORDER BY last_run ASC
            """, (now,)).fetchall()
        return [self._row_to_task(r) for r in rows]

    def mark_run(self, task_id: int):
        with self._conn() as c:
            c.execute(
                "UPDATE tasks SET last_run = ? WHERE id = ?",
                (time.time(), task_id)
            )
            c.commit()

    def toggle(self, name: str, enabled: bool):
        with self._conn() as c:
            c.execute(
                "UPDATE tasks SET enabled = ? WHERE name = ?",
                (int(enabled), name)
            )
            c.commit()

    def delete(self, name: str):
        with self._conn() as c:
            c.execute("DELETE FROM tasks WHERE name = ?", (name,))
            c.commit()
