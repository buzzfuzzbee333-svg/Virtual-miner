"""
Solpick.io — SOL faucet, Android task, 75s cooldown.

Flow:
  1. Navigate to faucet page
  2. Scroll in 5 passes of 900px; after each pass optionally close the CPX
     Research overlay (required=False so the step is silently skipped when
     the overlay is absent).
  3. Tap IconCaptcha to load icons, select the least-frequent icon.
  4. Tap the green Claim button, wait for success.

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
        "action":   "VISION_TAP",
        "prompt":   _CLOSE_OVERLAY_PROMPT,
        "save_to":  "/sdcard/sol_overlay.png",
        "required": False,
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

            # 2-6. Five scroll passes — close any CPX overlay after each
            _scroll(900), _wait(1), _close(), _wait(1),
            _scroll(900), _wait(1), _close(), _wait(1),
            _scroll(900), _wait(1), _close(), _wait(1),
            _scroll(900), _wait(1), _close(), _wait(1),
            _scroll(900), _wait(2), _close(), _wait(2),

            # 7. Tap the captcha area to activate it (may open a type-selector menu)
            {
                "action": "VISION_TAP",
                "prompt": (
                    "Find the captcha area near the bottom of the page. "
                    "It may appear as the IconCaptcha widget (blue shield + "
                    "'VERIFY THAT YOU ARE HUMAN') or as a captcha type selector button. "
                    "Tap it."
                ),
                "save_to":    "/sdcard/sol_captcha_start.png",
                "wait_after": 2,
            },

            # 8. If a captcha type-selector menu appeared, choose IconCaptcha
            {
                "action": "VISION_TAP",
                "prompt": (
                    "A captcha type selector or dropdown is now visible on screen with "
                    "options like 'IconCaptcha', 'reCaptcha', etc. "
                    "Tap the 'IconCaptcha' option to select it. "
                    "If no such menu is visible, respond with {\"x\": -1, \"y\": -1}."
                ),
                "save_to":    "/sdcard/sol_captcha_type.png",
                "required":   False,
                "wait_after": 3,
            },

            # 8. Select the icon that appears fewest times
            {
                "action": "VISION_TAP",
                "prompt": (
                    "The IconCaptcha is showing a row of small icon images. "
                    "Count how many times each unique icon appears across the row. "
                    "Tap the one icon that appears the fewest number of times."
                ),
                "save_to":    "/sdcard/sol_captcha_select.png",
                "wait_after": 2,
            },

            # 9. Tap the green Claim button
            {
                "action": "VISION_TAP",
                "prompt": (
                    "Find the green 'Claim' button. "
                    "It is a wide green rectangular button with white text reading 'Claim'. "
                    "Tap its center."
                ),
                "save_to":    "/sdcard/sol_claim_btn.png",
                "wait_after": 3,
            },

            # 10. Wait for success toast
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
