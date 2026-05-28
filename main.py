"""
Virtual Miner CLI
=================
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.registry import TaskRegistry
from core.logger import RunLogger
from core.scorer import Scorer
from core.scheduler import Scheduler
from core.validator import validate_task
from agent.agent import AutomationAgent


def cmd_status(_args):
    registry = TaskRegistry()

    print("\nTASKS")
    print("-" * 60)

    for task in registry.get_all():
        print(
            f"{task.name:<30} "
            f"{task.platform:<10} "
            f"{'ENABLED' if task.enabled else 'DISABLED'}"
        )


def cmd_generate(args):
    agent = AutomationAgent()

    task = agent.generate(args.prompt)

    validate_task(task)

    print(f"Generated: {task.name}")

    choice = input("Register task? [y/N]: ").strip().lower()

    if choice == "y":
        registry = TaskRegistry()
        registry.register(task)
        print("Saved.")


def cmd_run(args):
    registry = TaskRegistry()

    task = registry.get_by_name(args.name)

    if not task:
        print("Task not found")
        sys.exit(1)

    async def go():
        scheduler = Scheduler()
        await scheduler.run_task(task)

    asyncio.run(go())


def cmd_start(args):
    scheduler = Scheduler(
        poll_interval=args.poll,
        audit_interval=args.audit,
    )

    asyncio.run(scheduler.start())


def build_parser():
    parser = argparse.ArgumentParser()

    sub = parser.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("start")
    sp.add_argument("--poll", type=int, default=60)
    sp.add_argument("--audit", type=int, default=3600)

    rp = sub.add_parser("run")
    rp.add_argument("name")

    gp = sub.add_parser("generate")
    gp.add_argument("prompt")

    sub.add_parser("status")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "start": cmd_start,
        "run": cmd_run,
        "generate": cmd_generate,
        "status": cmd_status,
    }

    dispatch[args.command](args)


if __name__ == "__main__":
    main()
