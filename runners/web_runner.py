"""
Web Runner
==========
Async HTTP execution engine with debug logging + retries.
"""

import asyncio
import re

import httpx

_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 VirtualMiner/1.0"
}


class WebRunner:
    def __init__(self):
        self._clients = {}

    def _client(self, task_name):
        if task_name not in self._clients:
            self._clients[task_name] = httpx.AsyncClient(
                follow_redirects=True,
                timeout=30,
                headers=dict(_DEFAULT_HEADERS),
            )
        return self._clients[task_name]

    async def execute(self, task):
        client = self._client(task.name)

        ctx = {
            "last_response": None,
            "extracted": {},
            "earnings_usd": 0.0,
            "notes": "",
            "debug": {},
        }

        for idx, step in enumerate(task.flow.get("steps", [])):
            print(f"[STEP {idx}] {step['action']} -> {step}")
            await self._run_step(client, step, ctx)

        return {
            "earnings_usd": ctx["earnings_usd"],
            "notes": ctx["notes"],
        }

    async def _run_step(self, client, step, ctx):
        action = step["action"]

        retries = step.get("retry", 1)
        backoff = step.get("backoff_seconds", 2)

        for attempt in range(retries):
            try:
                if action == "GET":
                    ctx["last_response"] = await client.get(step["url"])

                elif action == "POST":
                    ctx["last_response"] = await client.post(
                        step["url"],
                        json=step.get("json"),
                        data=step.get("data"),
                    )

                elif action == "WAIT":
                    await asyncio.sleep(step.get("seconds", 1))

                elif action == "ASSERT_STATUS":
                    code = step.get("code", 200)
                    actual = ctx["last_response"].status_code
                    if actual != code:
                        raise RuntimeError(
                            f"Expected {code}, got {actual}"
                        )

                elif action == "ASSERT_TEXT":
                    body = ctx["last_response"].text
                    if step["contains"] not in body:
                        raise RuntimeError("ASSERT_TEXT failed")

                elif action == "EXTRACT_JSON":
                    data = ctx["last_response"].json()

                    for alias, path in step["mappings"].items():
                        val = data
                        for key in path.split("."):
                            val = val.get(key) if isinstance(val, dict) else None
                        ctx["extracted"][alias] = val

                elif action == "EXTRACT_REGEX":
                    match = re.search(
                        step["pattern"],
                        ctx["last_response"].text
                    )
                    ctx["extracted"][step["alias"]] = (
                        match.group(step.get("group", 1))
                        if match else None
                    )

                elif action == "SET_EARNINGS":
                    if "from_extracted" in step:
                        raw = ctx["extracted"].get(step["from_extracted"], 0)
                        ctx["earnings_usd"] = float(raw or 0)
                    else:
                        ctx["earnings_usd"] = float(step.get("value", 0))

                elif action == "SET_NOTE":
                    ctx["notes"] = step.get("text", "")

                elif action == "HEADER":
                    client.headers.update(step["headers"])

                return

            except Exception as e:
                ctx["debug"] = {
                    "error": str(e),
                    "step": step,
                }

                if attempt + 1 >= retries:
                    raise

                await asyncio.sleep(backoff)
