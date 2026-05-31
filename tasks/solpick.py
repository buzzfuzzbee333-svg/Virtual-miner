"""
Solpick.io — SOL faucet, Android task, 75s cooldown.

Flow:
  1. Navigate to faucet page.
  2. Scroll in 5 passes of 900px; after each pass optionally close any CPX
     Research overlay (required=False — silently skipped when absent).
  3. Scroll back UP 600px so the IconCaptcha widget is in the viewport
     (the 5 passes overshoot to the Claim button area).
  4. Tap the IconCaptcha widget to activate it, select the least-frequent
     icon image, then tap the Claim button.

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


def _scroll(amount=900, direction="up"):
    return {"action": "SCROLL", "direction": direction, "amount": amount}


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

            # 2-6. Five scroll passes to get past surveys; close any CPX overlay
            _scroll(900), _wait(1), _close(), _wait(1),
            _scroll(900), _wait(1), _close(), _wait(1),
            _scroll(900), _wait(1), _close(), _wait(1),
            _scroll(900), _wait(1), _close(), _wait(1),
            _scroll(900), _wait(2), _close(), _wait(2),

            # 7. Scroll back UP 600px — the 5 passes overshoot past the captcha
            #    to the Claim button; this brings the IconCaptcha widget into view.
            _scroll(600, direction="down"), _wait(2),

            # 8. Tap the IconCaptcha widget to activate and load icon images
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

            # 9. Select the icon that appears fewest times
            {
                "action": "VISION_TAP",
                "prompt": (
                    "The IconCaptcha is now showing a row of small icon images. "
                    "Count how many times each unique icon appears across the row. "
                    "Tap the one icon that appears the fewest number of times. "
                    "Do NOT tap any button or text — only tap one of the icon images."
                ),
                "save_to":    "/sdcard/sol_captcha_select.png",
                "wait_after": 2,
            },

            # 10. Tap the Claim / Claim Now button
            {
                "action": "VISION_TAP",
                "prompt": (
                    "Find the 'Claim' or 'Claim Now' button on the page. "
                    "It is a wide green or blue rectangular button with white text. "
                    "Tap its center."
                ),
                "save_to":    "/sdcard/sol_claim_btn.png",
                "wait_after": 3,
            },

            # 11. Wait for success toast
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
