"""
Web Runner — httpx async HTTP, Termux-safe, no Chromium needed.
Supports retry/backoff per step: {"action":"GET","url":"...","retry":2,"backoff_seconds":3}

Steps: GET, POST, WAIT, ASSERT_STATUS, ASSERT_TEXT,
       EXTRACT_JSON, EXTRACT_REGEX, SET_EARNINGS, SET_NOTE, HEADER
"""

import asyncio
import re

import httpx

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Mobile Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class WebRunner:
    def __init__(self):
        self._clients = {}

    def _client(self, task_name: str) -> httpx.AsyncClient:
        if task_name not in self._clients:
            self._clients[task_name] = httpx.AsyncClient(
                follow_redirects=True,
                timeout=30,
                headers=dict(_DEFAULT_HEADERS),
            )
        return self._clients[task_name]

    async def execute(self, task) -> dict:
        client = self._client(task.name)

        ctx: dict = {
            "last_response": None,
            "extracted":     {},
            "earnings_usd":  0.0,
            "notes":         "",
        }

        for idx, step in enumerate(task.flow.get("steps", [])):
            action  = step.get("action", "?")
            retries = max(step.get("retry", 1), 1)
            backoff = step.get("backoff_seconds", 2)

            for attempt in range(retries):
                try:
                    await self._run_step(client, step, ctx)
                    break
                except Exception as exc:
                    if attempt + 1 >= retries:
                        raise RuntimeError(
                            f"Step {idx} ({action}) failed after {attempt + 1} attempt(s): {exc}"
                        ) from exc
                    await asyncio.sleep(backoff)

        return {"earnings_usd": ctx["earnings_usd"], "notes": ctx["notes"]}

    async def _run_step(self, client: httpx.AsyncClient, step: dict, ctx: dict):
        action = step["action"]

        if action == "GET":
            ctx["last_response"] = await client.get(
                step["url"], params=step.get("params")
            )

        elif action == "POST":
            if "json" in step:
                ctx["last_response"] = await client.post(step["url"], json=step["json"])
            else:
                ctx["last_response"] = await client.post(step["url"], data=step.get("data"))

        elif action == "HEADER":
            client.headers.update(step["headers"])

        elif action == "WAIT":
            await asyncio.sleep(step.get("seconds", 1))

        elif action == "ASSERT_STATUS":
            expected = step.get("code", 200)
            actual   = ctx["last_response"].status_code
            if actual != expected:
                raise RuntimeError(f"ASSERT_STATUS: expected {expected}, got {actual}")

        elif action == "ASSERT_TEXT":
            if step["contains"] not in ctx["last_response"].text:
                raise RuntimeError(f"ASSERT_TEXT: '{step['contains']}' not found in response")

        elif action == "EXTRACT_JSON":
            data = ctx["last_response"].json()
            for alias, dot_path in step.get("mappings", {}).items():
                val = data
                for key in dot_path.split("."):
                    val = val.get(key) if isinstance(val, dict) else None
                ctx["extracted"][alias] = val

        elif action == "EXTRACT_REGEX":
            match = re.search(step["pattern"], ctx["last_response"].text)
            ctx["extracted"][step["alias"]] = (
                match.group(step.get("group", 1)) if match else None
            )

        elif action == "SET_EARNINGS":
            if "from_extracted" in step:
                raw = ctx["extracted"].get(step["from_extracted"], 0)
                ctx["earnings_usd"] = float(raw or 0)
            else:
                ctx["earnings_usd"] = float(step.get("value", 0))

        elif action == "SET_NOTE":
            ctx["notes"] = step.get("text", "")

        else:
            raise ValueError(f"Unknown web step action: '{action}'")
