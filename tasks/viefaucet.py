"""
Viefaucet.com — SOL faucet, Android task, 300s cooldown.

Observed flow (from screen recording):
  1. Navigate to faucet page
  2. Wait for page load
  3. Wait for claim section to appear
  4. Scroll down to captcha area
  5. Wait for captchas to render
  6. Vision sequence: click anti-bot word links in stated order
  7. Brief pause between interactions
  8. Vision tap: "I am not a robot" checkbox
  9. Wait for image captcha to appear
 10. Vision tap: upside-down image captcha
 11. Vision tap: Verify button
 12. Wait for success toast ("You have claimed")
 13. Set earnings (65 tokens ≈ $0.0001 at current SOL rate)

Run this file directly to register the task:
  python tasks/viefaucet.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.registry import Task, TaskRegistry

TASK = Task(
    name             = "viefaucet_sol_claim",
    platform         = "android",
    url              = "https://viefaucet.com/app/faucet",
    description      = "SOL faucet claim on Viefaucet.com every 5 minutes",
    cooldown_seconds = 300,
    tags             = ["faucet", "sol", "android", "5min"],
    flow             = {
        "steps": [
            {
                "action":       "NAVIGATE_URL",
                "url":          "https://viefaucet.com/app/faucet",
                "wait_seconds": 4,
            },
            {
                "action":  "WAIT_FOR_UI",
                "text":    "Verify",
                "timeout_seconds": 15,
            },
            {
                "action":    "SCROLL",
                "direction": "up",
                "amount":    400,
            },
            {
                "action":  "WAIT",
                "seconds": 2,
            },
            {
                "action": "VISION_SEQUENCE",
                "prompt": (
                    "This is a Viefaucet anti-bot challenge. "
                    "The page says 'Please click on the Anti-Bot links in the following order' "
                    "followed by several words. "
                    "Click each highlighted word link in the exact order stated. "
                    "Return the tap coordinates for each word link."
                ),
                "save_to":       "/sdcard/vie_antibot.png",
                "pause_between": 0.9,
            },
            {
                "action":  "WAIT",
                "seconds": 1,
            },
            {
                "action": "VISION_TAP",
                "prompt": (
                    "Find the 'I am not a robot' checkbox or similar anti-bot checkbox "
                    "and return its center coordinates."
                ),
                "save_to":    "/sdcard/vie_checkbox.png",
                "wait_after": 2,
            },
            {
                "action":  "WAIT",
                "seconds": 2,
            },
            {
                "action": "VISION_TAP",
                "prompt": (
                    "Find the image captcha that asks you to 'Select the upside down picture' "
                    "and tap the image that is upside down. "
                    "If no image is upside down, tap the 'NO ANSWER' option. "
                    "Return the center coordinates of your choice."
                ),
                "save_to":    "/sdcard/vie_captcha.png",
                "wait_after": 1,
            },
            {
                "action": "VISION_TAP",
                "prompt": (
                    "Find the 'Verify' button or submit button for the captcha challenge "
                    "and return its center coordinates."
                ),
                "save_to":    "/sdcard/vie_verify.png",
                "wait_after": 3,
            },
            {
                "action":          "WAIT_FOR_UI",
                "text":            "claimed",
                "timeout_seconds": 10,
                "required":        False,
            },
            {
                "action":  "WAIT",
                "seconds": 1,
            },
            {
                "action": "SET_EARNINGS",
                "value":  0.0001,
            },
            {
                "action": "SET_NOTE",
                "text":   "Viefaucet SOL claim — 65 tokens",
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
