import logging
import os
from datetime import datetime
from typing import Any

from escalation_engine.thread.extractors import (
    get_received_datetime,
    get_sender_address,
    parse_received_datetime,
)

logger = logging.getLogger(__name__)

CUSTOMER_ROLE = "customer"
ENGINEER_ROLE = "engineer"


def get_valid_messages(raw_thread: list[Any]) -> list[dict[str, Any]]:
    """
    Returns only dict-shaped messages from the raw thread.
    Does not normalize or transform their fields.
    """
    return [msg for msg in raw_thread if isinstance(msg, dict)]


def get_engineer_emails() -> set[str]:
    """
    Returns engineer email addresses configured for this deployment.

    Configure with a comma-separated ENGINEER_EMAILS environment variable.
    Example: ENGINEER_EMAILS=eng1@example.com,eng2@example.com
    """
    raw_value = os.getenv("ENGINEER_EMAILS", "")

    return {
        email.strip().lower()
        for email in raw_value.split(",")
        if email.strip()
    }


def is_engineer_message(message: dict[str, Any]) -> bool:
    sender_address = get_sender_address(message)

    if not sender_address:
        return False

    return sender_address.lower() in get_engineer_emails()


def get_message_role(message: dict[str, Any]) -> str:
    """Classify a canonical message using its configured sender address."""
    return ENGINEER_ROLE if is_engineer_message(message) else CUSTOMER_ROLE


def get_customer_messages(raw_thread: list[Any]) -> list[dict[str, Any]]:
    """
    Returns valid messages that were not sent by configured engineer emails.
    """
    return [
        message for message in get_valid_messages(raw_thread)
        if not is_engineer_message(message)
    ]


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
        if parse_received_datetime(msg) is not None
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

    parsed = parse_received_datetime({"receivedDateTime": value})

    if parsed is None:
        logger.warning("Unable to parse message receivedDateTime: %s", value)
        return datetime.min

    return parsed
