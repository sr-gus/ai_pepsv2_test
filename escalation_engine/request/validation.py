from typing import Any


def validate_request_body(req_body: Any) -> tuple[bool, str | None]:
    """
    Validates the minimum expected request structure.
    """
    if not isinstance(req_body, dict):
        return False, "Request body must be a JSON object"

    thread = req_body.get("thread")

    if not isinstance(thread, list) or len(thread) == 0:
        return False, "'thread' must be a non-empty array"

    valid_messages = [
        message for message in thread
        if isinstance(message, dict)
    ]

    if not valid_messages:
        return False, "'thread' must include at least one message object"

    return True, None
