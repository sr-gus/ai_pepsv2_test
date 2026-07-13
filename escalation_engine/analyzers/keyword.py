import logging
import re
from typing import Any

from escalation_engine.config import ESCALATION_CONFIG
from escalation_engine.thread.extractors import (
    get_message_text,
    get_preview,
    get_received_datetime,
    get_sender_address,
    get_subject,
)
from escalation_engine.thread.selectors import (
    get_customer_messages,
    get_latest_message,
    get_valid_messages,
)

logger = logging.getLogger(__name__)


async def analyze_keywords(raw_thread: list[Any]) -> dict[str, Any]:
    """
    Topic-based keyword analysis.

    Uses only the newest raw message in the thread.
    """
    logger.info("Starting keyword analysis. raw_thread_count=%s", len(raw_thread))

    valid_messages = get_valid_messages(raw_thread)
    customer_messages = get_customer_messages(raw_thread)
    ignored_engineer_messages = len(valid_messages) - len(customer_messages)

    logger.info(
        "Keyword analysis filtered messages. customer_message_count=%s ignored_engineer_message_count=%s",
        len(customer_messages),
        ignored_engineer_messages
    )

    latest_msg = get_latest_message(customer_messages)

    text = get_message_text(latest_msg)
    text = re.sub(r"[^\w\s]", " ", text.lower())
    words = text.split()

    topic_results = []
    triggered_topics = []
    total_matches = 0

    topic_config = ESCALATION_CONFIG["topics"]

    for topic, config in topic_config.items():
        keyword_matches = 0

        for keyword in config["keywords"]:
            keyword_matches += sum(
                1 for word in words
                if word == keyword.lower()
            )

        threshold = config["threshold"]
        triggered = keyword_matches >= threshold

        topic_result = {
            "topic": topic,
            "matches": keyword_matches,
            "threshold": threshold,
            "triggered": triggered
        }

        topic_results.append(topic_result)
        total_matches += keyword_matches

        if triggered:
            triggered_topics.append(topic)

    overall_trigger = len(triggered_topics) > 0

    word_count = max(len(words), 1)
    raw_score = total_matches / word_count
    score = min(raw_score * 5, 1.0)

    if overall_trigger:
        label = "triggered"
    elif score > 0.5:
        label = "moderate_signal"
    else:
        label = "low_signal"

    flags = []

    if overall_trigger:
        flags.append("keyword_trigger")

    if total_matches > 5:
        flags.append("high_keyword_density")

    result = {
        "name": "keyword",
        "score": round(score, 2),
        "label": label,
        "flags": flags,
        "details": {
            "analyzedMessage": {
                "received": get_received_datetime(latest_msg),
                "subject": get_subject(latest_msg),
                "preview": get_preview(latest_msg),
                "from": get_sender_address(latest_msg)
            },
            "topics": topic_results,
            "triggeredTopics": triggered_topics,
            "totalMatches": total_matches,
            "wordCount": len(words),
            "customerMessageCount": len(customer_messages),
            "ignoredEngineerMessageCount": ignored_engineer_messages
        }
    }

    logger.info(
        "Completed keyword analysis. score=%s label=%s total_matches=%s word_count=%s triggered_topics=%s flags=%s",
        result["score"],
        result["label"],
        total_matches,
        len(words),
        triggered_topics,
        flags
    )

    return result
