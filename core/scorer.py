"""
Scorer
======
Evaluates each task's health over a rolling window.
Computes a composite 0-100 score and recommends enable/disable.
Called by the scheduler periodically; can also be run manually.
"""

import sqlite3
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.registry import TaskRegistry

DB_PATH = Path(__file__).parent.parent / "data" / "miner.db"


class Scorer:
    MIN_SUCCESS_RATE  = 0.30
    MIN_DAILY_USD     = 0.001
    MIN_RUNS_TO_SCORE = 5

    EVAL_WINDOW_DAYS  = 7

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def score_task(self, task_name: str) -> dict:
        since = time.time() - (self.EVAL_WINDOW_DAYS * 86400)
        with self._conn() as c:
            rows = c.execute("""
                SELECT status,
                       COUNT(*)                      AS cnt,
                       COALESCE(SUM(earnings_usd), 0) AS earnings
                FROM runs
                WHERE task_name = ? AND timestamp >= ?
                GROUP BY status
            """, (task_name, since)).fetchall()

        counts = {"success": 0, "failure": 0, "skipped": 0}
        total_earned = 0.0
        for row in rows:
            counts[row["status"]] = row["cnt"]
            total_earned += row["earnings"]

        attempted = counts["success"] + counts["failure"]
        success_rate = counts["success"] / attempted if attempted else 0.0
        daily_usd    = total_earned / self.EVAL_WINDOW_DAYS

        rate_score  = success_rate * 50
        value_score = min(daily_usd / 0.01 * 50, 50)
        score       = round(rate_score + value_score, 1)

        recommendation = self._recommend(success_rate, daily_usd, attempted)

        return {
            "task_name":      task_name,
            "runs_attempted": attempted,
            "success_rate":   round(success_rate, 3),
            "daily_usd":      round(daily_usd, 6),
            "score":          score,
            "recommendation": recommendation,
        }

    def _recommend(
        self,
        success_rate: float,
        daily_usd: float,
        attempted: int,
    ) -> str:
        if attempted < self.MIN_RUNS_TO_SCORE:
            return "collecting_data"
        if success_rate < self.MIN_SUCCESS_RATE:
            return "disable:low_success"
        if daily_usd < self.MIN_DAILY_USD:
            return "disable:low_value"
        if success_rate >= 0.8 and daily_usd >= 0.05:
            return "high_performer"
        return "ok"

    def audit_all(self) -> list[dict]:
        with self._conn() as c:
            names = c.execute(
                "SELECT DISTINCT task_name FROM runs"
            ).fetchall()
        return [self.score_task(r["task_name"]) for r in names]

    def auto_disable(self, registry: "TaskRegistry") -> list[str]:
        disabled = []
        for s in self.audit_all():
            if s["recommendation"].startswith("disable"):
                registry.toggle(s["task_name"], False)
                disabled.append(s["task_name"])
        return disabled
