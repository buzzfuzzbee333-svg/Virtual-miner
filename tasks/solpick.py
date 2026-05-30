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
            {
                "action":       "NAVIGATE_URL",
                "url":          "https://solpick.io/faucet.php",
                "wait_seconds": 5,
            },
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
            {
                "action": "VISION_TAP",
                "prompt": (
                    "There is a CPX Research survey panel open on screen. "
                    "Find the X or × close/dismiss button for this panel. "
                    "It appears as a small × symbol in the top-left corner of the panel, "
                    "just above or inside the green CPX Research header bar. "
                    "Return the coordinates of that × close button."
                ),
                "save_to":    "/sdcard/sol_close_overlay.png",
                "wait_after": 2,
            },
            {
                "action": "VISION_TAP",
                "prompt": (
                    "This is an IconCaptcha. Find the row of small icon images. "
                    "Select (tap) the icon that appears the fewest number of times "
                    "compared to the others. Return its center coordinates."
                ),
                "save_to":    "/sdcard/sol_captcha.png",
                "wait_after": 1,
            },
            {
                "action":  "WAIT",
                "seconds": 1,
            },
            {
                "action": "VISION_TAP",
                "prompt": (
                    "Find the large blue claim button. It may say '+100% REWARDS', "
                    "'CLAIM', or show a reward percentage. "
                    "Return the center coordinates of this button."
                ),
                "save_to":    "/sdcard/sol_claim_btn.png",
                "wait_after": 3,
            },
            {
                "action":          "WAIT_FOR_UI",
                "text":            "Success",
                "timeout_seconds": 8,
                "required":        False,
            },
            {
                "action": "SET_EARNINGS",
                "value":  0.000162,
            },
            {
                "action": "SET_NOTE",
                "text":   "Solpick SOL claim — 0.000002 SOL",
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
