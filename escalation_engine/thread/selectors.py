import logging
import os
import re
from datetime import datetime
from typing import Any

from escalation_engine.thread.extractors import (
    get_headers,
    get_message_body_text,
    get_received_datetime,
    get_sender_address,
    get_subject,
    parse_received_datetime,
)

logger = logging.getLogger(__name__)

CUSTOMER_ROLE = "customer"
ENGINEER_ROLE = "engineer"
ENGINEER_EMAILS_ENV_VAR = "ENGINEER_EMAILS"

AUTO_REPLY_SUBJECT_KEYWORDS = (
    "out of office",
    "automatic reply",
    "auto-reply",
    "auto reply",
    "respuesta automática",
    "respuesta automatica",
    "undeliverable",
    "delivery status notification",
    "mail delivery failed",
    "returned mail",
    "auto-acknowledge",
    "auto acknowledgement",
    "ticket received",
    "ticket confirmation",
    "do not reply",
)
_AUTO_REPLY_HEADER_PATTERNS = (
    re.compile(
        r"\bauto-submitted\s*:\s*(?!no\b)(?:auto-generated|auto-replied|yes)\b",
        re.IGNORECASE
    ),
    re.compile(r"\bx-autoreply\s*:", re.IGNORECASE),
    re.compile(r"\bx-autorespond\s*:", re.IGNORECASE),
    re.compile(r"\bprecedence\s*:\s*(?:auto_reply|bulk)\b", re.IGNORECASE),
)
_AUTO_REPLY_BODY_PATTERNS = (
    re.compile(
        r"\bi am currently out of (?:the )?office\b",
        re.IGNORECASE
    ),
    re.compile(r"\bi(?:'|’)m (?:currently )?out of (?:the )?office\b", re.I),
    re.compile(r"\bi will be out of (?:the )?office\b", re.IGNORECASE),
    re.compile(r"\bi have limited access to (?:my )?email\b", re.IGNORECASE),
    re.compile(r"\bfuera de (?:la )?oficina\b", re.IGNORECASE),
    re.compile(r"\bno estar[eé] en (?:la )?oficina\b", re.IGNORECASE),
)


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

    The setting name is case-sensitive on platforms that expose environment
    variables with case-sensitive semantics. Addresses are comma-separated;
    matching itself is case-insensitive and ignores surrounding whitespace.
    """
    raw_value = os.getenv(ENGINEER_EMAILS_ENV_VAR, "")

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


def is_automatic_message(message: dict[str, Any]) -> bool:
    """Detect high-confidence automatic replies and delivery notifications."""
    subject = get_subject(message).lower()

    if any(keyword in subject for keyword in AUTO_REPLY_SUBJECT_KEYWORDS):
        return True

    headers_blob = _get_headers_blob(message)

    if any(pattern.search(headers_blob) for pattern in _AUTO_REPLY_HEADER_PATTERNS):
        return True

    current_body = get_message_body_text(message)

    return any(pattern.search(current_body) for pattern in _AUTO_REPLY_BODY_PATTERNS)


def get_non_automatic_messages(
    raw_thread: list[Any]
) -> list[dict[str, Any]]:
    """Return valid messages after removing detected automatic responses."""
    return [
        message for message in get_valid_messages(raw_thread)
        if not is_automatic_message(message)
    ]


def get_customer_messages(raw_thread: list[Any]) -> list[dict[str, Any]]:
    """
    Return non-automatic messages not sent by configured engineer emails.
    """
    return [
        message for message in get_non_automatic_messages(raw_thread)
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


def _get_headers_blob(message: dict[str, Any]) -> str:
    headers = get_headers(message)

    if isinstance(headers, dict):
        return "\n".join(f"{key}: {value}" for key, value in headers.items())

    if isinstance(headers, list):
        parts = []

        for header in headers:
            if isinstance(header, dict):
                name = header.get("name", "")
                value = header.get("value", "")
                parts.append(f"{name}: {value}")
            else:
                parts.append(str(header))

        return "\n".join(parts)

    return headers if isinstance(headers, str) else ""
