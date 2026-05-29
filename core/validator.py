"""
Flow Validator — validates task flows before execution.
"""

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


class FlowValidationError(Exception):
    pass


def validate_task(task):
    if task.platform not in ("web", "android"):
        raise FlowValidationError("Invalid platform")

    steps = task.flow.get("steps")
    if not isinstance(steps, list) or not steps:
        raise FlowValidationError("Task flow must contain steps")

    actions = WEB_ACTIONS if task.platform == "web" else ANDROID_ACTIONS

    for idx, step in enumerate(steps):
        action = step.get("action")

        if action not in actions:
            raise FlowValidationError(
                f"Unknown action '{action}' at step {idx}"
            )

        for field in actions[action]:
            if field not in step:
                raise FlowValidationError(
                    f"Missing required field '{field}' for action '{action}' at step {idx}"
                )

    return True
