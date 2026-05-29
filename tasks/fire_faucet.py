"""
FireFaucet.win — web task, hourly claim, 3600s cooldown.

Before registering:
  1. Create a free account at firefaucet.win
  2. Add credentials to config.json:
     { "fire_faucet": { "username": "...", "password": "..." } }
  3. Run:  python tasks/fire_faucet.py

Expected earnings: $1.50–$6 / month (hourly claim)

NOTE: The endpoints and payload shapes below are illustrative.
      Inspect actual network traffic with DevTools / mitmproxy and
      adjust to match the real request/response structure.

Run this file directly to register the task:
  python tasks/fire_faucet.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.registry import Task, TaskRegistry

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def _load_credentials() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"config.json not found at {CONFIG_PATH}. "
            "Copy config.example.json and fill in your credentials."
        )
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    return cfg.get("fire_faucet", {})


def build_task(username: str, password: str) -> Task:
    return Task(
        name             = "fire_faucet_claim",
        platform         = "web",
        url              = "https://firefaucet.win",
        description      = "Hourly faucet claim on FireFaucet.win",
        cooldown_seconds = 3600,
        tags             = ["faucet", "crypto", "web", "hourly"],
        flow             = {
            "steps": [
                # 1. Load login page (gets CSRF token / session cookie)
                {"action": "GET",           "url": "https://firefaucet.win/login"},
                {"action": "ASSERT_STATUS", "code": 200},

                # 2. Submit credentials
                {
                    "action": "POST",
                    "url":    "https://firefaucet.win/login",
                    "data":   {"username": username, "password": password},
                },
                {"action": "ASSERT_STATUS", "code": 200},
                {"action": "ASSERT_TEXT",   "contains": "dashboard"},

                # 3. Brief pause (mimic human navigation)
                {"action": "WAIT", "seconds": 2},

                # 4. Load faucet page
                {"action": "GET",           "url": "https://firefaucet.win/faucet"},
                {"action": "ASSERT_STATUS", "code": 200},
                {"action": "WAIT",          "seconds": 1},

                # 5. Submit claim
                {
                    "action": "POST",
                    "url":    "https://firefaucet.win/api/faucet/claim",
                    "json":   {"type": "faucet"},
                },
                {"action": "ASSERT_STATUS", "code": 200},

                # 6. Extract reward from JSON response (adjust dot-path to real API)
                {
                    "action":   "EXTRACT_JSON",
                    "mappings": {"reward": "data.reward_usd"},
                },

                # 7. Record result
                {"action": "SET_EARNINGS", "from_extracted": "reward"},
                {"action": "SET_NOTE",     "text": "FireFaucet hourly claim"},
            ]
        },
    )


def register():
    creds    = _load_credentials()
    username = creds.get("username", "")
    password = creds.get("password", "")

    if not username or not password:
        print(
            "[!] Missing fire_faucet credentials in config.json.\n"
            '    Add: { "fire_faucet": { "username": "...", "password": "..." } }'
        )
        sys.exit(1)

    task     = build_task(username, password)
    registry = TaskRegistry()
    registry.register(task)
    print(f"[✓] Registered task: {task.name}  (cooldown={task.cooldown_seconds}s)")


if __name__ == "__main__":
    register()
