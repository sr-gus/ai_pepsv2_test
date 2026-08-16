import logging
from collections import Counter
from typing import Any

from escalation_engine.thread.extractors import get_message_content, get_subject
from escalation_engine.thread.selectors import (
    get_non_automatic_messages,
    get_valid_messages,
)

logger = logging.getLogger(__name__)


async def analyze_sentimental(raw_thread: list[Any]) -> dict[str, Any]:
    """
    Placeholder sentimental analysis.

    This analyzer decides to use the full raw thread.
    """
    valid_messages = get_valid_messages(raw_thread)
    analyzed_messages = get_non_automatic_messages(raw_thread)
    extracted_contents = [
        get_message_content(message)
        for message in analyzed_messages
    ]

    logger.info(
        "Starting sentimental analysis. valid_message_count=%s analyzed_message_count=%s ignored_automatic_message_count=%s",
        len(valid_messages),
        len(analyzed_messages),
        len(valid_messages) - len(analyzed_messages)
    )

    full_text = " ".join(
        f"{get_subject(message)} {content.text}".strip()
        for message, content in zip(analyzed_messages, extracted_contents)
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
            "analyzedMessages": len(analyzed_messages),
            "ignoredAutomaticMessages": (
                len(valid_messages) - len(analyzed_messages)
            ),
            "textSources": dict(Counter(
                content.source for content in extracted_contents
            ))
        }
    }

    logger.info(
        "Completed sentimental analysis. score=%s label=%s flags=%s",
        result["score"],
        result["label"],
        result["flags"]
    )

    return result
