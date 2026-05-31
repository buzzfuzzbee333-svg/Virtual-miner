"""
Solpick.io — SOL faucet, Android task, 75s cooldown.

Flow:
  1. Navigate to faucet page.
  2. Tap the fixed Solpick header to give Chrome web-content keyboard focus.
  3. Use PAGE_DOWN keyevents (not swipe gestures) to scroll past the survey
     section. Keyboard events scroll the main page viewport and never interact
     with survey widget scroll containers, so they can't accidentally click
     survey items or get stuck scrolling inside a widget div.
  4. Close any CPX Research / survey overlay that appeared mid-scroll.
  5. Tap IconCaptcha, select the least-frequent icon, tap Claim.

Run this file directly to register the task:
  python tasks/solpick.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.registry import Task, TaskRegistry

_CLOSE_OVERLAY_PROMPT = (
    "Look for any popup, modal, or overlay currently covering the main page content. "
    "This could be a CPX Research survey panel, a country-selection survey, "
    "or any other panel sitting on top of the page. "
    "If an overlay IS present: find the closest close/dismiss button "
    "— an × or X, 'No thanks', 'Cancel', or 'Close'. Tap it. "
    "If NO overlay is visible, "
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


def _pgdn():
    # Scroll main page via keyboard — never touches survey widget scroll containers
    return {"action": "KEY", "keycode": 93}


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

            # 2. 2× PAGE_DOWN reaches the very bottom of the page.
            #    (Keyboard events don't trigger survey widget lazy-loading,
            #     so the page is short and 2 presses is enough.)
            _pgdn(), _wait(1),
            _pgdn(), _wait(2),

            # 4. Scroll back UP ~700px — the captcha is just above the
            #    Claim button which appears at the top after step 3.
            {"action": "SCROLL", "direction": "down", "amount": 700},
            _wait(1),
            _close(), _wait(1),

            # 4. Tap IconCaptcha to activate and load the icon images
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
                "wait_after": 7,
            },

            # 5. Select the icon that appears fewest times
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

            # 6. Tap the Claim / Claim Now button
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

            # 7. Wait for success toast
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
