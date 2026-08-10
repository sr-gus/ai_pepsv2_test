from datetime import datetime, timezone
from typing import Any


def get_subject(message: dict[str, Any]) -> str:
    value = message.get("subject")

    return value if isinstance(value, str) else ""


def get_preview(message: dict[str, Any]) -> str:
    value = message.get("bodyPreview")

    return value if isinstance(value, str) else ""


def get_sender_address(message: dict[str, Any]) -> str | None:
    sender = message.get("from")

    if not isinstance(sender, dict):
        return None

    email_address = sender.get("emailAddress")

    if not isinstance(email_address, dict):
        return None

    address = email_address.get("address")

    return address if isinstance(address, str) else None


def get_headers(message: dict[str, Any]) -> dict[str, Any] | str | None:
    value = message.get("headers")

    return value if isinstance(value, (dict, str)) else None


def get_received_datetime(message: dict[str, Any]) -> str | None:
    value = message.get("receivedDateTime")

    return value if isinstance(value, str) else None


def parse_received_datetime(message: dict[str, Any]) -> datetime | None:
    """Parse a message timestamp and normalize it to naive UTC."""
    value = get_received_datetime(message)

    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None

    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)

    return parsed


def get_message_text(message: dict[str, Any]) -> str:
    """
    Returns subject + body preview from a raw message.
    Useful for keyword or sentiment analysis.
    """
    return f"{get_subject(message)} {get_preview(message)}".strip()
