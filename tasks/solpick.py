"""
Solpick.io — SOL faucet, Android task, 75s cooldown.

Flow:
  1. Navigate to faucet page.
  2. Scroll 8 passes × 900px (7200px total) past the survey offerwall section.
     The first 3 passes close any CPX Research overlay after each scroll.
     Passes 4-8 scroll without overlay checks (surveys are behind us by then).
  3. Tap the IconCaptcha widget, select the least-frequent icon.
  4. Tap the Claim button.

Run this file directly to register the task:
  python tasks/solpick.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.registry import Task, TaskRegistry

_CLOSE_OVERLAY_PROMPT = (
    "Look for a CPX Research survey panel covering the page. "
    "If it is open, find its close button — a small × or X "
    "in the top-left corner just above the green CPX Research header bar. "
    "Tap it to dismiss the panel. "
    'If no overlay is visible, respond with {"x": -1, "y": -1}.'
)


def _close():
    return {
        "action":     "VISION_TAP",
        "prompt":     _CLOSE_OVERLAY_PROMPT,
        "save_to":    "/sdcard/sol_overlay.png",
        "required":   False,
        "wait_after": 1,
    }


def _scroll(amount=900):
    return {"action": "SCROLL", "direction": "up", "amount": amount}


def _wait(s=1):
    return {"action": "WAIT", "seconds": s}


TASK = Task(
    name             = "solpick_sol_claim",
    platform         = "android",
    url              = "https://solpick.io/faucet.php",
    description      = "SOL faucet claim on Solpick.io every 75 seconds",
    cooldown_seconds = 75,
    tags             = ["faucet", "sol", "android", "fast"],
    flow             = {
        "steps": [
            # 1. Load faucet page
            {
                "action":       "NAVIGATE_URL",
                "url":          "https://solpick.io/faucet.php",
                "wait_seconds": 5,
            },

            # Passes 1-3: scroll + close any CPX Research overlay
            _scroll(), _wait(1), _close(), _wait(1),
            _scroll(), _wait(1), _close(), _wait(1),
            _scroll(), _wait(1), _close(), _wait(1),

            # Passes 4-8: raw scrolls, no overlay check (past the survey zone)
            _scroll(), _wait(1),
            _scroll(), _wait(1),
            _scroll(), _wait(1),
            _scroll(), _wait(1),
            _scroll(), _wait(2),

            # 2. Tap IconCaptcha to activate it and load the icon images
            {
                "action": "VISION_TAP",
                "prompt": (
                    "Find the IconCaptcha widget. It is a rectangular box with "
                    "a blue shield icon on the left and text "
                    "'VERIFY THAT YOU ARE HUMAN' or 'IconCaptcha'. "
                    "Do NOT tap the Claim button or any survey widget. "
                    "Tap the center of the IconCaptcha box."
                ),
                "save_to":    "/sdcard/sol_captcha_start.png",
                "wait_after": 3,
            },

            # 3. Select the icon that appears fewest times
            {
                "action": "VISION_TAP",
                "prompt": (
                    "The IconCaptcha is showing a row of small icon images. "
                    "Count how many times each unique icon appears. "
                    "Tap the one icon that appears the fewest number of times."
                ),
                "save_to":    "/sdcard/sol_captcha_select.png",
                "wait_after": 2,
            },

            # 4. Tap the Claim / Claim Now button
            {
                "action": "VISION_TAP",
                "prompt": (
                    "Find the 'Claim' or 'Claim Now' button. "
                    "It is a wide green or blue rectangular button with white text. "
                    "Tap its center."
                ),
                "save_to":    "/sdcard/sol_claim_btn.png",
                "wait_after": 3,
            },

            # 5. Wait for success toast
            {
                "action":          "WAIT_FOR_UI",
                "text":            "Success",
                "timeout_seconds": 8,
                "required":        False,
            },
            {"action": "SET_EARNINGS", "value": 0.0000025},
            {"action": "SET_NOTE",     "text":  "Solpick SOL claim"},
        ]
    },
)


def register():
    registry = TaskRegistry()
    registry.register(TASK)
    print(f"[✓] Registered task: {TASK.name}  (cooldown={TASK.cooldown_seconds}s)")


if __name__ == "__main__":
    register()
