from typing import Any


def get_subject(message: dict[str, Any]) -> str:
    return message.get("subject") or ""


def get_preview(message: dict[str, Any]) -> str:
    return message.get("bodyPreview") or ""


def get_sender_address(message: dict[str, Any]) -> str | None:
    return (
        message
        .get("from", {})
        .get("emailAddress", {})
        .get("address")
    )


def get_received_datetime(message: dict[str, Any]) -> str | None:
    return message.get("receivedDateTime")


def get_message_text(message: dict[str, Any]) -> str:
    """
    Returns subject + body preview from a raw message.
    Useful for keyword or sentiment analysis.
    """
    return f"{get_subject(message)} {get_preview(message)}".strip()