"""
Virtual Miner CLI
=================
Commands: start  status  scores  run  toggle  payout  generate  chat
"""

import argparse
import asyncio
import importlib.util
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.registry import TaskRegistry
from core.logger import RunLogger
from core.scorer import Scorer
from core.scheduler import Scheduler

_TASKS_DIR = Path(__file__).parent / "tasks"


def _refresh_tasks():
    """Import every tasks/*.py and re-register its TASK object into the DB."""
    registry = TaskRegistry()
    for task_file in sorted(_TASKS_DIR.glob("*.py")):
        if task_file.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location("_vm_task", task_file)
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "TASK"):
                registry.register(mod.TASK)
        except Exception as exc:
            print(f"  [warn] could not load {task_file.name}: {exc}")


def cmd_status(_args):
    _refresh_tasks()
    registry = TaskRegistry()
    logger = RunLogger()

    tasks = registry.get_all()
    summary = logger.summary(days=30)

    print(f"\nTASKS  ({len(tasks)} registered)")
    print("-" * 72)
    print(f"  {'NAME':<28} {'PLATFORM':<10} {'STATE':<10} {'RUNS':<6} EARNED (30d)")
    print("-" * 72)

    for task in tasks:
        ts = summary["tasks"].get(task.name, {})
        runs = ts.get("success", 0) + ts.get("failure", 0)
        earned = ts.get("earnings_usd", 0.0)
        state = "ENABLED" if task.enabled else "DISABLED"
        print(f"  {task.name:<28} {task.platform:<10} {state:<10} {runs:<6} ${earned:.5f}")

    print("-" * 72)
    print(f"  Total confirmed payouts (30d): ${summary['payout_total_usd']:.5f}")

    recent = logger.recent(limit=6)
    if recent:
        print(f"\nRECENT RUNS")
        print("-" * 72)
        for r in recent:
            ts = time.strftime("%m-%d %H:%M", time.localtime(r["timestamp"]))
            note = (r["notes"] or "")[:32]
            print(f"  {ts}  {r['task_name']:<26} {r['status']:<10} ${r['earnings_usd']:.5f}  {note}")


def cmd_scores(_args):
    scorer = Scorer()
    scores = scorer.audit_all()

    if not scores:
        print("No run history yet.")
        return

    print(f"\nSCORES  (7-day rolling window)")
    print("-" * 80)
    print(f"  {'TASK':<28} {'SCORE':<7} {'RUNS':<6} {'SUCCESS%':<10} {'$/day':<10} RECOMMEND")
    print("-" * 80)

    for s in sorted(scores, key=lambda x: x["score"], reverse=True):
        print(
            f"  {s['task_name']:<28} {s['score']:<7} {s['runs_attempted']:<6}"
            f" {s['success_rate']*100:<10.1f} {s['daily_usd']:<10.5f} {s['recommendation']}"
        )


def cmd_run(args):
    _refresh_tasks()
    registry = TaskRegistry()
    task = registry.get_by_name(args.name)

    if not task:
        print(f"Task '{args.name}' not found.")
        sys.exit(1)

    async def go():
        scheduler = Scheduler()
        record = await scheduler.run_task(task)
        print(f"\nResult: {record.status}  earnings=${record.earnings_usd:.5f}  notes={record.notes}")

    asyncio.run(go())


def cmd_toggle(args):
    registry = TaskRegistry()
    task = registry.get_by_name(args.name)

    if not task:
        print(f"Task '{args.name}' not found.")
        sys.exit(1)

    new_state = not task.enabled
    registry.toggle(args.name, new_state)
    print(f"'{args.name}' is now {'ENABLED' if new_state else 'DISABLED'}.")


def cmd_payout(args):
    logger = RunLogger()
    logger.log_payout(
        task_name=args.task,
        amount_usd=float(args.amount),
        method=args.method or "",
        notes=args.notes or "",
    )
    print(f"Payout logged: ${args.amount:.5f} from '{args.task}'")


def cmd_generate(args):
    from agent.agent import AutomationAgent
    agent = AutomationAgent()

    spec = agent.generate(args.prompt)

    if args.register:
        agent._save_and_register(spec)
        print(f"Generated and registered: {spec['name']}")
    else:
        agent._display_spec(spec)
        choice = input("Register task? [y/N]: ").strip().lower()
        if choice == "y":
            agent._save_and_register(spec)
            print("Saved.")


def cmd_chat(_args):
    from agent.agent import AutomationAgent
    agent = AutomationAgent()
    agent.interactive()


def cmd_start(args):
    _refresh_tasks()
    scheduler = Scheduler(
        poll_interval=args.poll,
        audit_interval=args.audit,
        task_timeout=args.timeout,
    )
    asyncio.run(scheduler.start())


def build_parser():
    parser = argparse.ArgumentParser(description="Virtual Miner")
    sub = parser.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("start", help="Run scheduler loop")
    sp.add_argument("--poll",    type=int, default=60,   help="Poll interval (seconds)")
    sp.add_argument("--audit",   type=int, default=3600, help="Scorer audit interval (seconds)")
    sp.add_argument("--timeout", type=int, default=120,  help="Per-task timeout (seconds)")

    sub.add_parser("status", help="Show tasks and recent runs")
    sub.add_parser("scores", help="Profitability audit")

    rp = sub.add_parser("run", help="Run one task immediately")
    rp.add_argument("name")

    tp = sub.add_parser("toggle", help="Enable/disable a task")
    tp.add_argument("name")

    pp = sub.add_parser("payout", help="Log a confirmed manual payout")
    pp.add_argument("task")
    pp.add_argument("amount", type=float)
    pp.add_argument("--method", default="", help="Withdrawal method label")
    pp.add_argument("--notes",  default="", help="Optional notes")

    gp = sub.add_parser("generate", help="Generate a task spec with the agent")
    gp.add_argument("prompt")
    gp.add_argument("--register", action="store_true", help="Register immediately without prompting")

    sub.add_parser("chat", help="Interactive agent REPL")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "start":    cmd_start,
        "status":   cmd_status,
        "scores":   cmd_scores,
        "run":      cmd_run,
        "toggle":   cmd_toggle,
        "payout":   cmd_payout,
        "generate": cmd_generate,
        "chat":     cmd_chat,
    }

    dispatch[args.command](args)


if __name__ == "__main__":
    main()
