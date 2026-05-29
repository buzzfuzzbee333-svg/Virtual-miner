"""
Scheduler
=========
Async task orchestrator with timeout protection.
"""

import asyncio
import time

from core.registry import TaskRegistry
from core.logger import RunLogger, RunRecord
from core.scorer import Scorer
from core.state import TaskStateStore
from runners.web_runner import WebRunner
from runners.android_runner import AndroidRunner


class Scheduler:
    def __init__(
        self,
        poll_interval=60,
        audit_interval=3600,
        task_timeout=120,
    ):
        self.registry = TaskRegistry()
        self.logger = RunLogger()
        self.scorer = Scorer()
        self.state = TaskStateStore()

        self.web_runner = WebRunner()
        self.android_runner = AndroidRunner()

        self.poll_interval = poll_interval
        self.audit_interval = audit_interval
        self.task_timeout = task_timeout

        self._last_audit = 0
        self._running = False

        self._semaphore = asyncio.Semaphore(3)

    async def run_task(self, task):
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
                print(f"[RUN] {task.name}")

                result = await asyncio.wait_for(
                    runner.execute(task),
                    timeout=self.task_timeout
                )

                record.status = "success"
                record.earnings_usd = result.get("earnings_usd", 0)
                record.notes = result.get("notes", "")

                state = self.state.get(task.name)
                state["last_success"] = time.time()
                state["failure_streak"] = 0
                self.state.set(task.name, state)

            except Exception as e:
                record.notes = str(e)

                state = self.state.get(task.name)
                state["failure_streak"] = (
                    state.get("failure_streak", 0) + 1
                )
                self.state.set(task.name, state)

            self.logger.log(record)
            self.registry.mark_run(task.id)

            return record

    async def tick(self):
        due = self.registry.get_due()

        if not due:
            print(f"[IDLE] sleeping {self.poll_interval}s")
            return

        await asyncio.gather(
            *[self.run_task(t) for t in due]
        )

        if time.time() - self._last_audit >= self.audit_interval:
            disabled = self.scorer.auto_disable(self.registry)

            if disabled:
                print(f"[AUTO-DISABLED] {disabled}")

            self._last_audit = time.time()

    async def start(self):
        self._running = True

        while self._running:
            await self.tick()
            await asyncio.sleep(self.poll_interval)

    def stop(self):
        self._running = False
