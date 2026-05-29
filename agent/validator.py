"""
Spec Validator — validates raw agent-generated spec dicts before registry write.
"""

import re

REQUIRED_TOP = ["name", "platform", "cooldown_seconds", "flow"]

WEB_ACTIONS = {
    "GET":           ["url"],
    "POST":          ["url"],
    "HEADER":        ["headers"],
    "WAIT":          [],
    "ASSERT_STATUS": ["code"],
    "ASSERT_TEXT":   ["contains"],
    "EXTRACT_JSON":  ["mappings"],
    "EXTRACT_REGEX": ["pattern", "alias"],
    "SET_EARNINGS":  [],
    "SET_NOTE":      [],
}

ANDROID_ACTIONS = {
    "NAVIGATE_URL":    ["url"],
    "LAUNCH_APP":      ["package"],
    "CLEAR_APP":       ["package"],
    "TAP":             ["x", "y"],
    "TAP_UI":          [],
    "SWIPE":           ["x1", "y1", "x2", "y2"],
    "SCROLL":          [],
    "TYPE":            ["text"],
    "KEY":             ["keycode"],
    "WAIT":            [],
    "WAIT_FOR_UI":     [],
    "SCREENSHOT":      [],
    "VISION_TAP":      ["prompt"],
    "VISION_SEQUENCE": ["prompt"],
    "SET_EARNINGS":    [],
    "SET_NOTE":        [],
}

_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")


class SpecValidationError(ValueError):
    pass


def validate_spec(spec: dict) -> bool:
    if not isinstance(spec, dict):
        raise SpecValidationError("Spec must be a JSON object")

    for key in REQUIRED_TOP:
        if key not in spec:
            raise SpecValidationError(f"Missing required field: '{key}'")

    name = spec["name"]
    if not isinstance(name, str) or not _SNAKE_CASE.match(name):
        raise SpecValidationError(
            f"'name' must be snake_case (letters/digits/underscores, starts with letter). Got: {name!r}"
        )

    platform = spec["platform"]
    if platform not in ("web", "android"):
        raise SpecValidationError(f"'platform' must be 'web' or 'android', got: {platform!r}")

    cooldown = spec["cooldown_seconds"]
    if not isinstance(cooldown, (int, float)) or cooldown < 60:
        raise SpecValidationError(
            f"'cooldown_seconds' must be a number ≥ 60, got: {cooldown!r}"
        )

    flow = spec.get("flow", {})
    steps = flow.get("steps")
    if not isinstance(steps, list) or not steps:
        raise SpecValidationError("'flow.steps' must be a non-empty list")

    actions = WEB_ACTIONS if platform == "web" else ANDROID_ACTIONS

    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            raise SpecValidationError(f"Step {idx} must be a dict")

        action = step.get("action")
        if action not in actions:
            raise SpecValidationError(
                f"Unknown action '{action}' at step {idx} for platform '{platform}'"
            )

        for field in actions[action]:
            if field not in step:
                raise SpecValidationError(
                    f"Step {idx} ({action}): missing required field '{field}'"
                )

    return True
