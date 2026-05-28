"""
Android Runner
==============
Automates Android apps via ADB from Termux.

Setup (one-time):
  1. Enable Developer Options on your device
     Settings → About Phone → tap Build Number 7×
  2. Enable Wireless Debugging
     Developer Options → Wireless Debugging → ON
  3. Pair via Termux (first time only):
     adb pair <ip>:<port>   # use the pairing code shown on screen
  4. Connect:
     adb connect localhost:5555
     (or adb connect <ip>:5555 if connecting from another machine)
  5. Verify:
     adb devices

Install ADB in Termux:
  pkg install android-tools

Flow steps supported:
  LAUNCH_APP     – start an Activity by package/activity name
  TAP            – tap absolute screen coords
  TAP_UI         – find element by text/content-desc, tap its center
  SWIPE          – swipe gesture
  TYPE           – type text into focused field
  KEY            – send a keyevent code (e.g. 4 = BACK, 3 = HOME)
  WAIT           – sleep N seconds
  WAIT_FOR_UI    – poll UI dump until element appears (or timeout)
  SCREENSHOT     – screencap to /sdcard/
  CLEAR_APP      – clear app data / force-stop
  SET_EARNINGS   – write earnings_usd
  SET_NOTE       – write notes
"""

import asyncio
import re
from typing import Optional


class AndroidRunner:
    # Change this if you use a different ADB target
    DEFAULT_DEVICE = "localhost:5555"

    def __init__(self, device: str = DEFAULT_DEVICE):
        self.device = device

    # ------------------------------------------------------------------ #
    # Entry point                                                          #
    # ------------------------------------------------------------------ #

    async def execute(self, task) -> dict:
        context = {
            "extracted":    {},
            "earnings_usd": 0.0,
            "notes":        "",
        }
        for step in task.flow.get("steps", []):
            await self._run_step(step, context)
        return {
            "earnings_usd": context["earnings_usd"],
            "notes":        context["notes"],
        }

    # ------------------------------------------------------------------ #
    # Step dispatcher                                                      #
    # ------------------------------------------------------------------ #

    async def _run_step(self, step: dict, ctx: dict):
        action = step["action"]

        if action == "LAUNCH_APP":
            pkg      = step["package"]
            activity = step.get("activity", "")
            if activity:
                await self._adb(f"shell am start -n {pkg}/{activity}")
            else:
                await self._adb(
                    f"shell monkey -p {pkg} -c android.intent.category.LAUNCHER 1"
                )

        elif action == "CLEAR_APP":
            await self._adb(f"shell pm clear {step['package']}")

        elif action == "TAP":
            await self._adb(f"shell input tap {step['x']} {step['y']}")

        elif action == "TAP_UI":
            await self._tap_element(
                text=step.get("text"),
                content_desc=step.get("content_desc"),
                resource_id=step.get("resource_id"),
            )

        elif action == "SWIPE":
            ms = step.get("duration_ms", 300)
            await self._adb(
                f"shell input swipe "
                f"{step['x1']} {step['y1']} {step['x2']} {step['y2']} {ms}"
            )

        elif action == "TYPE":
            # Spaces must be encoded as %s for ADB input text
            encoded = step["text"].replace(" ", "%s")
            await self._adb(f"shell input text {encoded}")

        elif action == "KEY":
            await self._adb(f"shell input keyevent {step['keycode']}")

        elif action == "WAIT":
            await asyncio.sleep(step.get("seconds", 1))

        elif action == "WAIT_FOR_UI":
            found = await self._wait_for_element(
                text=step.get("text"),
                content_desc=step.get("content_desc"),
                resource_id=step.get("resource_id"),
                timeout=step.get("timeout_seconds", 10),
            )
            if not found and step.get("required", True):
                raise RuntimeError(
                    f"WAIT_FOR_UI timed out: {step}"
                )

        elif action == "SCREENSHOT":
            path = step.get("save_to", "/sdcard/miner_cap.png")
            await self._adb(f"shell screencap -p {path}")

        elif action == "SET_EARNINGS":
            ctx["earnings_usd"] = float(step.get("value", 0.0))

        elif action == "SET_NOTE":
            ctx["notes"] = step.get("text", "")

        else:
            raise ValueError(f"Unknown android step action: '{action}'")

    # ------------------------------------------------------------------ #
    # ADB helpers                                                          #
    # ------------------------------------------------------------------ #

    async def _adb(self, cmd: str) -> str:
        full = f"adb -s {self.device} {cmd}"
        proc = await asyncio.create_subprocess_shell(
            full,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            err = stderr.decode().strip()
            raise RuntimeError(f"ADB failed ({full!r}): {err}")
        return stdout.decode().strip()

    async def _dump_ui(self) -> str:
        """Dump UI hierarchy to stdout and return it."""
        return await self._adb("shell uiautomator dump /dev/tty")

    async def _wait_for_element(
        self,
        text:         Optional[str] = None,
        content_desc: Optional[str] = None,
        resource_id:  Optional[str] = None,
        timeout:      int = 10,
    ) -> bool:
        for _ in range(timeout):
            try:
                dump = await self._dump_ui()
                if self._find_bounds(dump, text, content_desc, resource_id):
                    return True
            except Exception:
                pass
            await asyncio.sleep(1)
        return False

    async def _tap_element(
        self,
        text:         Optional[str] = None,
        content_desc: Optional[str] = None,
        resource_id:  Optional[str] = None,
    ):
        dump   = await self._dump_ui()
        bounds = self._find_bounds(dump, text, content_desc, resource_id)
        if bounds is None:
            identifier = text or content_desc or resource_id
            raise RuntimeError(f"UI element not found: '{identifier}'")
        x1, y1, x2, y2 = bounds
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        await self._adb(f"shell input tap {cx} {cy}")

    @staticmethod
    def _find_bounds(
        dump:         str,
        text:         Optional[str],
        content_desc: Optional[str],
        resource_id:  Optional[str],
    ) -> Optional[tuple[int, int, int, int]]:
        """
        Parse a uiautomator dump for an element matching any of the
        provided attributes. Returns (x1, y1, x2, y2) or None.
        """
        # Build a pattern that matches the target attribute followed
        # (eventually) by a bounds attribute on the same node.
        def make_pattern(attr: str, value: str) -> str:
            return (
                rf'{attr}="{re.escape(value)}"'
                r'(?:[^>]*?)bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
            )

        candidates = []
        if text:
            candidates.append(make_pattern("text", text))
        if content_desc:
            candidates.append(make_pattern("content-desc", content_desc))
        if resource_id:
            candidates.append(make_pattern("resource-id", resource_id))

        for pattern in candidates:
            m = re.search(pattern, dump, re.DOTALL)
            if m:
                return tuple(map(int, m.groups()))

        return None
