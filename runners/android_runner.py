"""
Android Runner — ADB automation + Claude Vision captcha solving.

Setup: pkg install android-tools && adb connect localhost:5555

Step types:
  NAVIGATE_URL    — open URL in Chrome via ADB intent
  LAUNCH_APP      — start app by package name
  CLEAR_APP       — pm clear + force-stop
  TAP / TAP_UI    — tap by absolute coords or UI element text
  SWIPE / SCROLL  — gesture helpers
  TYPE / KEY      — text input and keycodes
  WAIT / WAIT_FOR_UI — timing helpers
  SCREENSHOT      — screencap to /sdcard/
  VISION_TAP      — screenshot → Claude Vision → single tap
  VISION_SEQUENCE — screenshot → Claude Vision → ordered tap sequence
  SET_EARNINGS / SET_NOTE — result recording
"""

import asyncio
import os
import re
import time
from typing import Optional

_TMPDIR = os.environ.get("TMPDIR", "/data/data/com.termux/files/usr/tmp")


class AndroidRunner:
    DEFAULT_DEVICE = "localhost:5555"

    def __init__(self, device: str = DEFAULT_DEVICE):
        self.device = device
        self._screen_size: Optional[tuple[int, int]] = None

    async def execute(self, task) -> dict:
        ctx = {"extracted": {}, "earnings_usd": 0.0, "notes": ""}
        for step in task.flow.get("steps", []):
            await self._run_step(step, ctx)
        return {"earnings_usd": ctx["earnings_usd"], "notes": ctx["notes"]}

    async def _run_step(self, step: dict, ctx: dict):
        action = step["action"]

        if action == "NAVIGATE_URL":
            url = step["url"]
            await self._adb(
                f'shell am start -a android.intent.action.VIEW '
                f'-d "{url}" com.android.chrome'
            )
            await asyncio.sleep(step.get("wait_seconds", 3))

        elif action == "LAUNCH_APP":
            pkg = step["package"]
            if step.get("activity"):
                await self._adb(f"shell am start -n {pkg}/{step['activity']}")
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

        elif action == "SCROLL":
            w, h = await self._get_screen_size()
            cx     = w // 2
            amount = step.get("amount", 500)
            if step.get("direction", "up") == "up":
                await self._adb(
                    f"shell input swipe {cx} {h//2 + amount//2} {cx} {h//2 - amount//2} 900"
                )
            else:
                await self._adb(
                    f"shell input swipe {cx} {h//2 - amount//2} {cx} {h//2 + amount//2} 900"
                )

        elif action == "TYPE":
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
                raise RuntimeError(f"WAIT_FOR_UI timed out: {step}")

        elif action == "SCREENSHOT":
            path = step.get("save_to", "/sdcard/miner_cap.png")
            await self._adb(f"shell screencap -p {path}")

        elif action == "VISION_TAP":
            await self._vision_tap(step)

        elif action == "VISION_SEQUENCE":
            await self._vision_sequence(step)

        elif action == "SET_EARNINGS":
            ctx["earnings_usd"] = float(step.get("value", 0.0))

        elif action == "SET_NOTE":
            ctx["notes"] = step.get("text", "")

        else:
            raise ValueError(f"Unknown android step action: '{action}'")

    # ------------------------------------------------------------------ #
    # Vision helpers                                                       #
    # ------------------------------------------------------------------ #

    async def _vision_tap(self, step: dict):
        from agent.vision_solver import VisionSolver
        required = step.get("required", True)
        remote = step.get("save_to", "/sdcard/vision_cap.png")
        ts     = int(time.time())
        local  = f"{_TMPDIR}/vm_cap_{ts}.png"
        await self._adb(f"shell screencap -p {remote}")
        await self._adb(f"pull {remote} {local}")
        print(f"    [vision] screenshot saved → {local}")
        solver = VisionSolver()
        try:
            x_frac, y_frac = await solver.single_tap(local, step["prompt"])
        except RuntimeError as exc:
            if not required:
                print(f"    [vision] optional tap skipped — {exc}")
                return
            raise
        w, h = await self._get_screen_size()
        px, py = int(x_frac * w), int(y_frac * h)
        print(f"    [vision] tap → ({px}, {py})  screen=({w}x{h})")
        # negative or out-of-bounds coordinates mean Vision signalled "not found"
        if px <= 0 or py <= 0 or px >= w or py >= h:
            msg = f"Vision returned out-of-bounds ({px},{py}) — element not found"
            if not required:
                print(f"    [vision] optional tap skipped — {msg}")
                return
            raise RuntimeError(msg)
        await self._adb(f"shell input tap {px} {py}")
        if "wait_after" in step:
            await asyncio.sleep(step["wait_after"])

    async def _vision_sequence(self, step: dict):
        from agent.vision_solver import VisionSolver
        remote = step.get("save_to", "/sdcard/vision_seq.png")
        local  = f"{_TMPDIR}/vm_seq_{int(time.time())}.png"
        await self._adb(f"shell screencap -p {remote}")
        await self._adb(f"pull {remote} {local}")
        solver = VisionSolver()
        taps = await solver.tap_sequence(local, step["prompt"])
        w, h = await self._get_screen_size()
        pause = step.get("pause_between", 0.8)
        for i, (x_frac, y_frac) in enumerate(taps):
            px, py = int(x_frac * w), int(y_frac * h)
            print(f"    [vision seq {i+1}/{len(taps)}] tap → ({px}, {py})")
            await self._adb(f"shell input tap {px} {py}")
            await asyncio.sleep(pause)

    # ------------------------------------------------------------------ #
    # ADB helpers                                                          #
    # ------------------------------------------------------------------ #

    async def _adb(self, cmd: str) -> str:
        proc = await asyncio.create_subprocess_shell(
            f"adb -s {self.device} {cmd}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            err = stderr.decode().strip()
            raise RuntimeError(f"ADB failed ({cmd!r}): {err}")
        return stdout.decode().strip()

    async def _get_screen_size(self) -> tuple[int, int]:
        if self._screen_size:
            return self._screen_size
        out = await self._adb("shell wm size")
        dims = out.split(":")[-1].strip()
        w, h = map(int, dims.split("x"))
        self._screen_size = (w, h)
        return self._screen_size

    async def _dump_ui(self) -> str:
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
        text:         Optional[str] = None,
        content_desc: Optional[str] = None,
        resource_id:  Optional[str] = None,
    ) -> Optional[tuple[int, int, int, int]]:
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
