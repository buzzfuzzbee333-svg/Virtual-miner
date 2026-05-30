"""
Scheduler — async loop, semaphore(3), per-task timeout, scorer audit.
"""

import asyncio
import json
import time
from pathlib import Path

from core.registry import TaskRegistry
from core.logger import RunLogger, RunRecord
from core.scorer import Scorer
from core.state import TaskStateStore
from runners.web_runner import WebRunner
from runners.android_runner import AndroidRunner

MAX_CONCURRENT = 3
_CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def _adb_device() -> str:
    try:
        cfg = json.loads(_CONFIG_PATH.read_text())
        return cfg.get("android", {}).get("device", "localhost:5555")
    except Exception:
        return "localhost:5555"


class Scheduler:
    def __init__(
        self,
        poll_interval: int = 60,
        audit_interval: int = 3600,
        task_timeout: int = 120,
    ):
        self.registry       = TaskRegistry()
        self.logger         = RunLogger()
        self.scorer         = Scorer()
        self.state          = TaskStateStore()
        self.web_runner     = WebRunner()
        self.android_runner = AndroidRunner(device=_adb_device())

        self.poll_interval  = poll_interval
        self.audit_interval = audit_interval
        self.task_timeout   = task_timeout

        self._last_audit = 0.0
        self._running    = False
        self._semaphore  = asyncio.Semaphore(MAX_CONCURRENT)

    async def run_task(self, task) -> RunRecord:
        async with self._semaphore:
            runner = (
                self.web_runner
                if task.platform == "web"
                else self.android_runner
            )

            record = RunRecord(
                task_id=task.id,
                task_name=task.name,
                status="failure",
            )

            try:
                print(f"  [→] {task.name}")

                result = await asyncio.wait_for(
                    runner.execute(task),
                    timeout=self.task_timeout,
                )

                record.status       = "success"
                record.earnings_usd = result.get("earnings_usd", 0.0)
                record.notes        = result.get("notes", "")

                self.state.reset_failure_streak(task.name)
                print(f"  [✓] {task.name}  ${record.earnings_usd:.5f}  {record.notes}")

            except asyncio.TimeoutError:
                record.notes = f"Timed out after {self.task_timeout}s"
                streak = self.state.increment_failure_streak(task.name)
                print(f"  [✗] {task.name}  TIMEOUT  (streak={streak})")

            except Exception as exc:
                record.notes = str(exc)
                streak = self.state.increment_failure_streak(task.name)
                print(f"  [✗] {task.name}  {exc}  (streak={streak})")

            self.logger.log(record)
            self.registry.mark_run(task.id)

            return record

    async def tick(self):
        due = self.registry.get_due()

        if not due:
            print(f"[·] No tasks due — sleeping {self.poll_interval}s")
            return

        print(f"\n[⏱] {len(due)} task(s) due")
        await asyncio.gather(
            *[self.run_task(t) for t in due],
            return_exceptions=True,
        )

        if time.time() - self._last_audit >= self.audit_interval:
            disabled = self.scorer.auto_disable(self.registry)
            if disabled:
                print(f"[⚠] Auto-disabled: {disabled}")
            self._last_audit = time.time()

    async def start(self):
        self._running = True
        print(
            f"[*] Scheduler started  "
            f"poll={self.poll_interval}s  "
            f"timeout={self.task_timeout}s  "
            f"concurrency={MAX_CONCURRENT}"
        )
        while self._running:
            await self.tick()
            await asyncio.sleep(self.poll_interval)

    def stop(self):
        self._running = False
