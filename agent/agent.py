"""
Automation Engineer Agent
=========================
Uses Anthropic API (claude-sonnet) for natural-language → validated task flow generation.

Methods:
  generate(description)    — single-shot spec generation
  interactive()            — REPL: describe → review → [r]egister/[e]dit/[j]son/[d]iscard
  _call(messages)          — raw Anthropic API call (httpx, no SDK required)
  _display_spec(spec)      — pretty-print flow review table
  _save_and_register(spec) — write JSON to tasks/ + register in DB
"""

import json
import os
from pathlib import Path

import httpx

from core.registry import Task, TaskRegistry
from agent.validator import validate_spec, SpecValidationError
from agent.prompts import SYSTEM_PROMPT

CONFIG_PATH = Path(__file__).parent.parent / "config.json"
TASKS_DIR   = Path(__file__).parent.parent / "tasks"
API_URL     = "https://api.anthropic.com/v1/messages"
MODEL       = "claude-sonnet-4-20250514"


class AutomationAgent:
    def __init__(self):
        self._api_key = self._load_key()

    def _load_key(self) -> str:
        key = ""
        try:
            cfg = json.loads(CONFIG_PATH.read_text())
            key = cfg.get("agent", {}).get("api_key", "")
        except FileNotFoundError:
            pass
        key = key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key or key.startswith("YOUR"):
            raise ValueError(
                "Anthropic API key missing.\n"
                "  Option 1: set config.json → agent.api_key\n"
                "  Option 2: export ANTHROPIC_API_KEY=sk-ant-..."
            )
        return key

    # ------------------------------------------------------------------ #
    # API                                                                  #
    # ------------------------------------------------------------------ #

    def _call(self, messages: list[dict]) -> str:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                API_URL,
                headers={
                    "Content-Type":      "application/json",
                    "x-api-key":         self._api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model":      MODEL,
                    "max_tokens": 4096,
                    "system":     SYSTEM_PROMPT,
                    "messages":   messages,
                },
            )
            resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    @staticmethod
    def _parse(raw: str) -> dict:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            end   = -1 if lines[-1].strip() == "```" else len(lines)
            text  = "\n".join(lines[1:end])
        return json.loads(text)

    # ------------------------------------------------------------------ #
    # Public interface                                                     #
    # ------------------------------------------------------------------ #

    def generate(self, description: str) -> dict:
        messages = [{"role": "user", "content": description}]
        raw  = self._call(messages)
        spec = self._parse(raw)
        validate_spec(spec)
        return spec

    def interactive(self):
        print("Virtual Miner — Agent REPL")
        print("Describe a task in plain language. Type 'exit' to quit.")
        print("Built-in commands: clear  list  exit\n")

        registry  = TaskRegistry()
        history:  list[dict] = []
        last_spec: dict | None = None

        while True:
            try:
                user_input = input("You> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not user_input:
                continue

            if user_input == "exit":
                break

            if user_input == "clear":
                history.clear()
                last_spec = None
                print("[cleared]")
                continue

            if user_input == "list":
                tasks = registry.get_all()
                if tasks:
                    for t in tasks:
                        state = "on" if t.enabled else "off"
                        print(f"  {t.name:<30} [{t.platform}] {state}")
                else:
                    print("  (no tasks registered)")
                continue

            history.append({"role": "user", "content": user_input})

            try:
                raw = self._call(history)
                history.append({"role": "assistant", "content": raw})

                spec = self._parse(raw)
                validate_spec(spec)
                last_spec = spec

                self._display_spec(spec)
                print("Actions: [r]egister  [e]dit  [j]son  [d]iscard")

                action = input("> ").strip().lower()

                if action == "r":
                    self._save_and_register(spec)
                    print(f"[registered] {spec['name']}")
                    last_spec = None

                elif action == "j":
                    print(json.dumps(spec, indent=2))

                elif action == "e":
                    edit_input = input("Describe changes: ").strip()
                    if edit_input:
                        history.append({"role": "user", "content": edit_input})

                elif action == "d":
                    history = history[:-2]
                    last_spec = None
                    print("[discarded]")

            except json.JSONDecodeError as exc:
                print(f"[parse error] {exc}")
                if history and history[-1]["role"] == "assistant":
                    print(f"Raw: {history[-1]['content'][:300]}")
                    history.pop()
                if history and history[-1]["role"] == "user":
                    history.pop()

            except SpecValidationError as exc:
                print(f"[validation error] {exc}")
                if history and history[-1]["role"] == "assistant":
                    history.pop()
                if history and history[-1]["role"] == "user":
                    history.pop()

            except httpx.HTTPStatusError as exc:
                print(f"[API error] {exc.response.status_code}: {exc.response.text[:200]}")
                if history and history[-1]["role"] == "user":
                    history.pop()

            except Exception as exc:
                print(f"[error] {exc}")
                if history and history[-1]["role"] == "user":
                    history.pop()

    # ------------------------------------------------------------------ #
    # Display / storage                                                    #
    # ------------------------------------------------------------------ #

    def _display_spec(self, spec: dict):
        name     = spec.get("name", "(unnamed)")
        platform = spec.get("platform", "?")
        cooldown = spec.get("cooldown_seconds", "?")

        print(f"\n{'='*62}")
        print(f"  {name}  [{platform}]  cooldown={cooldown}s")
        if spec.get("description"):
            print(f"  {spec['description']}")
        if spec.get("url"):
            print(f"  URL: {spec['url']}")
        if spec.get("tags"):
            print(f"  Tags: {', '.join(spec['tags'])}")
        print(f"{'='*62}")

        steps = spec.get("flow", {}).get("steps", [])
        for i, step in enumerate(steps):
            action  = step.get("action", "?")
            details = {k: v for k, v in step.items() if k != "action"}
            detail_str = "  ".join(
                f"{k}={json.dumps(v)}" for k, v in list(details.items())[:4]
            )
            print(f"  [{i:2d}] {action:<20} {detail_str}")
        print()

    def _save_and_register(self, spec: dict) -> Task:
        TASKS_DIR.mkdir(parents=True, exist_ok=True)

        name = spec["name"]
        (TASKS_DIR / f"{name}.json").write_text(json.dumps(spec, indent=2))

        task = Task(
            name             = name,
            platform         = spec["platform"],
            cooldown_seconds = int(spec.get("cooldown_seconds", 3600)),
            flow             = spec["flow"],
            enabled          = True,
            url              = spec.get("url"),
            description      = spec.get("description", ""),
            tags             = spec.get("tags", []),
        )
        TaskRegistry().register(task)
        return task
