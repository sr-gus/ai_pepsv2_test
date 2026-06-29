import logging
from typing import Any

from escalation_engine.thread.extractors import get_message_text
from escalation_engine.thread.selectors import get_valid_messages

logger = logging.getLogger(__name__)


async def analyze_sentimental(raw_thread: list[Any]) -> dict[str, Any]:
    """
    Placeholder sentimental analysis.

    This analyzer decides to use the full raw thread.
    """
    valid_messages = get_valid_messages(raw_thread)

    logger.info(
        "Starting sentimental analysis. valid_message_count=%s",
        len(valid_messages)
    )

    full_text = " ".join(
        get_message_text(message)
        for message in valid_messages
    )

    # Placeholder:
    # Later this full_text can be sent to a real sentiment model.
    _ = full_text

    result = {
        "name": "sentimental",
        "score": 0.82,
        "label": "negative",
        "confidence": 0.9,
        "flags": ["frustration_detected"],
        "details": {
            "analyzedMessages": len(valid_messages)
        }
    }

    logger.info(
        "Completed sentimental analysis. score=%s label=%s flags=%s",
        result["score"],
        result["label"],
        result["flags"]
    )

    return result