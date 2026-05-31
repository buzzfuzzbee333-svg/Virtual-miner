"""
Solpick.io — SOL faucet, Android task, 75s cooldown.

Flow:
  1. Navigate to faucet page.
  2. Scroll 7 passes × 900px (6300px total).
     Passes 1-4 close any overlay (CPX Research, country surveys, etc.)
     Passes 5-7 are raw scrolls (past the survey section by then).
  3. Tap the IconCaptcha widget, select the least-frequent icon.
  4. Tap the Claim button.

Run this file directly to register the task:
  python tasks/solpick.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.registry import Task, TaskRegistry

# General overlay close: handles CPX Research, country-selection surveys,
# or any other modal that covers the page during scrolling.
_CLOSE_OVERLAY_PROMPT = (
    "Look for any popup, modal, or overlay currently covering the main page content. "
    "This could be a CPX Research survey panel, a country-selection survey "
    "('Are you from the United States?'), or any other panel sitting on top of the page. "
    "If an overlay IS present: find the closest thing to a close/dismiss button "
    "— an × or X, a 'No thanks', 'Cancel', or 'Close' label, or any small button "
    "in a corner of the overlay. Tap it. "
    "If NO overlay is visible (the main Solpick faucet page is showing normally), "
    'respond with {"x": -1, "y": -1}.'
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

            # Passes 1-4: scroll + close any overlay that appears
            _scroll(), _wait(1), _close(), _wait(1),
            _scroll(), _wait(1), _close(), _wait(1),
            _scroll(), _wait(1), _close(), _wait(1),
            _scroll(), _wait(1), _close(), _wait(1),

            # Passes 5-7: raw scrolls — past all survey widgets by now
            _scroll(), _wait(1),
            _scroll(), _wait(1),
            _scroll(), _wait(2),

            # 2. Tap IconCaptcha to activate and load the icon images
            {
                "action": "VISION_TAP",
                "prompt": (
                    "Find the IconCaptcha widget on screen. It is a small rectangular "
                    "box with a blue shield/circle icon on the left and text "
                    "'VERIFY THAT YOU ARE HUMAN' or 'IconCaptcha'. "
                    "It is NOT the Claim button and NOT a survey widget. "
                    "Tap the center of the IconCaptcha box to activate it."
                ),
                "save_to":    "/sdcard/sol_captcha_start.png",
                "wait_after": 3,
            },

            # 3. Select the icon that appears fewest times
            {
                "action": "VISION_TAP",
                "prompt": (
                    "The IconCaptcha is now showing a row of small icon images. "
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
