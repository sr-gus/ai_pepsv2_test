import logging
from typing import Any

from escalation_engine.thread.conditioning import (
    build_sentiment_transcript,
)

logger = logging.getLogger(__name__)


async def analyze_sentimental(raw_thread: list[Any]) -> dict[str, Any]:
    """
    Placeholder sentimental analysis.

    This analyzer conditions the full accumulated thread for the future model.
    """
    conditioned = build_sentiment_transcript(raw_thread)

    logger.info(
        "Starting sentimental analysis. analyzed_message_count=%s "
        "conditioned_turn_count=%s ignored_automatic_message_count=%s",
        conditioned.analyzed_messages,
        conditioned.included_turns,
        conditioned.ignored_automatic_messages,
    )

    full_text = conditioned.text

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
            "analyzedMessages": conditioned.analyzed_messages,
            "ignoredAutomaticMessages": (
                conditioned.ignored_automatic_messages
            ),
            "conditionedTurns": conditioned.included_turns,
            "textSources": conditioned.text_sources,
        }
    }

    logger.info(
        "Completed sentimental analysis. score=%s label=%s flags=%s",
        result["score"],
        result["label"],
        result["flags"]
    )

    return result
