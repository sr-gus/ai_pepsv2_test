import logging
from datetime import datetime
from typing import Any

from escalation_engine.thread.extractors import get_received_datetime

logger = logging.getLogger(__name__)


def get_valid_messages(raw_thread: list[Any]) -> list[dict[str, Any]]:
    """
    Returns only dict-shaped messages from the raw thread.
    Does not normalize or transform their fields.
    """
    return [msg for msg in raw_thread if isinstance(msg, dict)]


def get_latest_message(raw_thread: list[Any]) -> dict[str, Any]:
    """
    Returns the newest raw message based on receivedDateTime.
    Falls back to the last valid message if timestamps are missing or invalid.
    """
    valid_messages = get_valid_messages(raw_thread)

    if not valid_messages:
        return {}

    messages_with_received = [
        msg for msg in valid_messages
        if get_received_datetime(msg)
    ]

    if not messages_with_received:
        logger.warning(
            "No messages with receivedDateTime found. Falling back to last valid message."
        )
        return valid_messages[-1]

    latest_message = max(
        messages_with_received,
        key=lambda message: _parse_datetime(get_received_datetime(message))
    )

    logger.info(
        "Latest message selected. received=%s",
        get_received_datetime(latest_message)
    )

    return latest_message


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.min

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        logger.warning("Unable to parse message receivedDateTime: %s", value)
        return datetime.min