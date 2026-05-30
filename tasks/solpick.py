"""
Solpick.io — SOL faucet, Android task, 75s cooldown.

Observed flow (from screen recording):
  1. Navigate to faucet page
  2. Wait for page load
  3. Scroll down past level progress bar and survey offerwalls
  4. Wait for IconCaptcha to render
  5. Vision tap: IconCaptcha — select image shown fewest times
  6. Wait for captcha validation
  7. Vision tap: "+100% REWARDS" button (large blue claim button)
  8. Wait for success toast ("Success! You got 0.000002000 SOL!")
  9. Set earnings (0.000002 SOL ≈ $0.000162 at SOL = $81)

Run this file directly to register the task:
  python tasks/solpick.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.registry import Task, TaskRegistry

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
            # 2. Scroll down past survey widgets to captcha area
            {
                "action":    "SCROLL",
                "direction": "up",
                "amount":    700,
            },
            {
                "action":  "WAIT",
                "seconds": 1,
            },
            {
                "action":    "SCROLL",
                "direction": "up",
                "amount":    700,
            },
            {
                "action":  "WAIT",
                "seconds": 2,
            },
            # 3. Close CPX Research survey overlay triggered by scrolling
            {
                "action": "VISION_TAP",
                "prompt": (
                    "A CPX Research survey panel is open on screen covering the page. "
                    "Find the × or X close button to dismiss it. "
                    "It is a small × in the top-left corner just above the green "
                    "CPX Research header bar. Tap it to close the panel."
                ),
                "save_to":    "/sdcard/sol_close_overlay.png",
                "wait_after": 2,
            },
            # 4. Scroll further down to reach the captcha area (past survey section)
            {
                "action":    "SCROLL",
                "direction": "up",
                "amount":    900,
            },
            {
                "action":  "WAIT",
                "seconds": 2,
            },
            # 5. Tap the captcha widget to start it (loads icon images)
            {
                "action": "VISION_TAP",
                "prompt": (
                    "Find the IconCaptcha widget. It shows a blue circular icon "
                    "and text saying 'VERIFY THAT YOU ARE HUMAN' or 'IconCaptcha'. "
                    "Tap the blue circle or the widget area to start the captcha "
                    "and load the icon images."
                ),
                "save_to":    "/sdcard/sol_captcha_start.png",
                "wait_after": 3,
            },
            # 5. Select the correct icon (appears fewest times)
            {
                "action": "VISION_TAP",
                "prompt": (
                    "The IconCaptcha is now showing a row of small icon images. "
                    "Count how many times each unique icon appears. "
                    "Tap the icon that appears the fewest number of times."
                ),
                "save_to":    "/sdcard/sol_captcha_select.png",
                "wait_after": 2,
            },
            # 6. Tap the green Claim button
            {
                "action": "VISION_TAP",
                "prompt": (
                    "Find the green 'Claim' button on the page. "
                    "It is a wide green rectangular button with white text that says 'Claim'. "
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
            {
                "action": "SET_EARNINGS",
                "value":  0.0000025,
            },
            {
                "action": "SET_NOTE",
                "text":   "Solpick SOL claim",
            },
        ]
    },
)


def register():
    registry = TaskRegistry()
    registry.register(TASK)
    print(f"[✓] Registered task: {TASK.name}  (cooldown={TASK.cooldown_seconds}s)")


if __name__ == "__main__":
    register()
