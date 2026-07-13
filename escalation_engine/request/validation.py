from typing import Any


def extract_thread(req_body: Any) -> list[Any] | None:
    """
    Returns the thread from supported request shapes.

    Supported payloads:
    - {"thread": [...]}
    - {"body": {"thread": [...]}}
    """
    if not isinstance(req_body, dict):
        return None

    thread = req_body.get("thread")

    if isinstance(thread, list):
        return thread

    body = req_body.get("body")

    if isinstance(body, dict):
        nested_thread = body.get("thread")

        if isinstance(nested_thread, list):
            return nested_thread

    return None


def validate_request_body(req_body: Any) -> tuple[bool, str | None]:
    """
    Validates the minimum expected request structure.
    """
    if not isinstance(req_body, dict):
        return False, "Request body must be a JSON object"

    thread = extract_thread(req_body)

    if not isinstance(thread, list) or len(thread) == 0:
        return False, "'thread' must be a non-empty array at root or body.thread"

    valid_messages = [
        message for message in thread
        if isinstance(message, dict)
    ]

    if not valid_messages:
        return False, "'thread' must include at least one message object"

    return True, None