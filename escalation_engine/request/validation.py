from typing import Any


def validate_request_body(req_body: dict[str, Any]) -> tuple[bool, str | None]:
    """
    Validates the minimum expected request structure.
    """
    thread = req_body.get("thread")

    if not isinstance(thread, list) or len(thread) == 0:
        return False, "'thread' must be a non-empty array"

    return True, None