import logging
from typing import Any

from escalation_engine.thread.extractors import get_received_datetime
from escalation_engine.thread.selectors import get_valid_messages

logger = logging.getLogger(__name__)


async def analyze_frequency(raw_thread: list[Any]) -> dict[str, Any]:
    """
    Placeholder frequency analysis.

    This analyzer decides to inspect timestamps across the raw thread.
    """
    valid_messages = get_valid_messages(raw_thread)

    received_values = [
        get_received_datetime(message)
        for message in valid_messages
        if get_received_datetime(message)
    ]

    logger.info(
        "Starting frequency analysis. valid_message_count=%s messages_with_timestamp=%s",
        len(valid_messages),
        len(received_values)
    )

    result = {
        "name": "frequency",
        "score": 0.6,
        "label": "increasing",
        "flags": ["rapid_followup"],
        "details": {
            "messagesPerDay": len(valid_messages),
            "messagesWithTimestamp": len(received_values),
            "ghostedHours": 24
        }
    }

    logger.info(
        "Completed frequency analysis. score=%s label=%s flags=%s",
        result["score"],
        result["label"],
        result["flags"]
    )

    return result