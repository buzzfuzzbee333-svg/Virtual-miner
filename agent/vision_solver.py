"""
Vision Solver — screenshot → Anthropic Vision API → tap coordinates.
Coordinates returned as fractions (0.0–1.0) of screen dimensions.

Methods:
  single_tap(image_path, prompt)   → (x_frac, y_frac)
  tap_sequence(image_path, prompt) → [(x1, y1), (x2, y2), ...]
"""

import base64
import json
from pathlib import Path

import httpx

CONFIG_PATH = Path(__file__).parent.parent / "config.json"
API_URL     = "https://api.anthropic.com/v1/messages"
MODEL       = "claude-sonnet-4-20250514"

_COORD_SUFFIX = (
    "\n\nRespond ONLY with valid JSON. "
    'Format: {"x": 0.5, "y": 0.3} '
    "where values are fractions (0.0 = left/top, 1.0 = right/bottom)."
)
_SEQ_SUFFIX = (
    "\n\nRespond ONLY with valid JSON. "
    'Format: {"taps": [{"x": 0.2, "y": 0.6}, {"x": 0.5, "y": 0.6}]}'
)


class VisionSolver:
    def __init__(self):
        cfg = json.loads(CONFIG_PATH.read_text())
        key = cfg.get("agent", {}).get("api_key", "")
        if not key or key.startswith("YOUR"):
            raise ValueError(
                "Anthropic API key missing in config.json → agent.api_key"
            )
        self._key = key

    async def _call(self, image_path: str, prompt: str) -> str:
        img_b64 = base64.b64encode(Path(image_path).read_bytes()).decode()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                API_URL,
                headers={
                    "Content-Type":      "application/json",
                    "x-api-key":         self._key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model":      MODEL,
                    "max_tokens": 256,
                    "messages": [{
                        "role":    "user",
                        "content": [
                            {
                                "type":   "image",
                                "source": {
                                    "type":       "base64",
                                    "media_type": "image/png",
                                    "data":       img_b64,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }],
                },
            )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    @staticmethod
    def _parse_json(raw: str) -> dict:
        text = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        start = text.find("{")
        end   = text.rfind("}") + 1
        return json.loads(text[start:end])

    async def single_tap(self, image_path: str, prompt: str) -> tuple[float, float]:
        raw    = await self._call(image_path, prompt + _COORD_SUFFIX)
        result = self._parse_json(raw)
        x = result.get("x")
        y = result.get("y")
        if x is None or y is None:
            raise RuntimeError(f"Vision: element not found. Response: {raw[:200]}")
        return float(x), float(y)

    async def tap_sequence(
        self, image_path: str, prompt: str
    ) -> list[tuple[float, float]]:
        raw    = await self._call(image_path, prompt + _SEQ_SUFFIX)
        result = self._parse_json(raw)
        return [(float(t["x"]), float(t["y"])) for t in result["taps"]]
