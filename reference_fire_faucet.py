"""
Fire Faucet Task
================
Reference implementation showing how to define a web-platform task.

Before registering:
  1. Create a free account at https://firefaucet.win
  2. Copy your credentials into config.json (never hardcode them here)
  3. Run:  python tasks/fire_faucet.py

Expected earnings:  $1.50 – $6 / month  (hourly claim)
Cooldown:           3 600 s  (1 hour)

NOTE: The exact API endpoints and payload shapes below are illustrative.
      Inspect the real site's network traffic (DevTools / mitmproxy) and
      adjust the steps to match actual request/response structure.
"""

import json
import sys
from pathlib import Path

# Allow running this file directly from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.registry import Task, TaskRegistry

# ── Credentials ─────────────────────────────────────────────────────────────
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


# ── Task definition ──────────────────────────────────────────────────────────

def build_task(username: str, password: str) -> Task:
    return Task(
        name             = "fire_faucet_claim",
        platform         = "web",
        url              = "https://firefaucet.win",
        cooldown_seconds = 3600,   # 1 hour
        description      = "Hourly faucet claim on FireFaucet.win",
        tags             = ["faucet", "crypto", "web", "hourly"],
        flow             = {
            "steps": [
                # 1. Load login page (gets CSRF token / session cookie)
                {
                    "action": "GET",
                    "url":    "https://firefaucet.win/login",
                },
                {"action": "ASSERT_STATUS", "code": 200},

                # 2. Submit credentials
                {
                    "action": "POST",
                    "url":    "https://firefaucet.win/login",
                    "data": {
                        "username": username,
                        "password": password,
                    },
                },
                # Successful login typically redirects to dashboard (200 or 302→200)
                {"action": "ASSERT_STATUS", "code": 200},
                {"action": "ASSERT_TEXT",   "contains": "dashboard"},   # adjust to real marker

                # 3. Brief pause (mimic human navigation)
                {"action": "WAIT", "seconds": 2},

                # 4. Load faucet page
                {
                    "action": "GET",
                    "url":    "https://firefaucet.win/faucet",
                },
                {"action": "ASSERT_STATUS", "code": 200},
                {"action": "WAIT", "seconds": 1},

                # 5. Submit claim
                {
                    "action": "POST",
                    "url":    "https://firefaucet.win/api/faucet/claim",
                    "json":   {"type": "faucet"},
                },
                {"action": "ASSERT_STATUS", "code": 200},

                # 6. Pull reward value from JSON response
                #    Adjust the dot-path to match real API response shape
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


# ── Registration helper ──────────────────────────────────────────────────────

def register():
    creds    = _load_credentials()
    username = creds.get("username", "")
    password = creds.get("password", "")

    if not username or not password:
        print(
            "[!] Missing fire_faucet credentials in config.json.\n"
            "    Add: { \"fire_faucet\": { \"username\": \"...\", \"password\": \"...\" } }"
        )
        sys.exit(1)

    task     = build_task(username, password)
    registry = TaskRegistry()
    registry.register(task)
    print(f"[✓] Registered task: {task.name}  (cooldown={task.cooldown_seconds}s)")


if __name__ == "__main__":
    register()
