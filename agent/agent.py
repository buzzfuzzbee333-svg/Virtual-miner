"""
Automation Engineer Agent
=========================
Natural language -> validated task flow generator.
"""

import json
import os
from pathlib import Path

import google.generativeai as genai

from core.registry import Task
from core.validator import validate_task

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

SYSTEM_PROMPT = """
You are the Automation Engineer Agent.

Generate ONLY valid JSON task definitions.

Rules:
- Output JSON only
- Use only supported DSL actions
- No captchas
- No secret values
- One workflow only
- Prefer deterministic flows
"""


class AutomationAgent:
    def __init__(self):
        self._setup()

    def _setup(self):
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)

        api_key = (
            cfg.get("agent", {}).get("api_key")
            or os.environ.get("GEMINI_API_KEY")
        )

        if not api_key:
            raise ValueError("Missing API key")

        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT,
            generation_config={
                "response_mime_type": "application/json"
            }
        )

    def generate(self, prompt: str):
        response = self.model.generate_content(prompt)
        data = json.loads(response.text)

        task = Task(
            name=data["name"],
            platform=data["platform"],
            cooldown_seconds=data.get("cooldown_seconds", 3600),
            flow=data["flow"],
            enabled=True,
            url=data.get("url"),
            description=data.get("description", ""),
            tags=data.get("tags", []),
        )

        validate_task(task)

        return task
