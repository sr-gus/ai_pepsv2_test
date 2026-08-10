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

    subject_text = _normalize_text(get_subject(latest_msg))
    preview_text = _normalize_text(get_preview(latest_msg))
    text = _normalize_text(get_message_text(latest_msg))
    words = text.split()

    topic_results = []
    triggered_topics = []
    total_matches = 0

    topic_config = ESCALATION_CONFIG["topics"]

    for topic, config in topic_config.items():
        topic_match = _analyze_topic_matches(
            subject_text,
            preview_text,
            config
        )

        threshold = config["threshold"]
        triggered = topic_match["weightedMatches"] >= threshold

        topic_result = {
            "topic": topic,
            "matches": topic_match["matches"],
            "weightedMatches": topic_match["weightedMatches"],
            "uniqueMatches": topic_match["uniqueMatches"],
            "keywordMatches": topic_match["keywordMatches"],
            "phraseMatches": topic_match["phraseMatches"],
            "criticalPhraseMatches": topic_match["criticalPhraseMatches"],
            "threshold": threshold,
            "triggered": triggered
        }

        topic_results.append(topic_result)
        total_matches += topic_match["matches"]

        if triggered:
            triggered_topics.append(topic)

    overall_trigger = len(triggered_topics) > 0

    word_count = max(len(words), 1)
    weighted_total_matches = sum(
        topic["weightedMatches"]
        for topic in topic_results
    )
    total_unique_matches = len({
        match
        for topic in topic_results
        for match in topic["uniqueMatches"]
    })
    raw_score = weighted_total_matches / word_count
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

    if weighted_total_matches > 5:
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
            "weightedTotalMatches": weighted_total_matches,
            "totalUniqueMatches": total_unique_matches,
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


def _normalize_text(value: str) -> str:
    return re.sub(r"[^\w\s]", " ", value.lower())


def _analyze_topic_matches(
    subject_text: str,
    preview_text: str,
    config: dict[str, Any]
) -> dict[str, Any]:
    keyword_matches = []
    phrase_matches = []
    critical_phrase_matches = []
    unique_matches = set()
    weighted_matches = 0

    for keyword in config.get("keywords", []):
        normalized_keyword = _normalize_text(keyword).strip()

        if not normalized_keyword:
            continue

        subject_count = _count_word_matches(subject_text, normalized_keyword)
        preview_count = _count_word_matches(preview_text, normalized_keyword)
        total_count = subject_count + preview_count

        if total_count == 0:
            continue

        unique_matches.add(normalized_keyword)
        weighted_matches += subject_count * 2 + preview_count
        keyword_matches.append({
            "value": normalized_keyword,
            "subjectMatches": subject_count,
            "previewMatches": preview_count,
            "matches": total_count
        })

    for phrase in config.get("phrases", []):
        normalized_phrase = _normalize_text(phrase).strip()

        if not normalized_phrase:
            continue

        subject_count = _count_phrase_matches(subject_text, normalized_phrase)
        preview_count = _count_phrase_matches(preview_text, normalized_phrase)
        total_count = subject_count + preview_count

        if total_count == 0:
            continue

        unique_matches.add(normalized_phrase)
        weighted_matches += subject_count * 2 + preview_count
        phrase_matches.append({
            "value": normalized_phrase,
            "subjectMatches": subject_count,
            "previewMatches": preview_count,
            "matches": total_count
        })

    for phrase in config.get("critical_phrases", []):
        normalized_phrase = _normalize_text(phrase).strip()

        if not normalized_phrase:
            continue

        subject_count = _count_phrase_matches(subject_text, normalized_phrase)
        preview_count = _count_phrase_matches(preview_text, normalized_phrase)
        total_count = subject_count + preview_count

        if total_count == 0:
            continue

        unique_matches.add(normalized_phrase)
        weighted_matches += (subject_count * 2 + preview_count) * 2
        critical_phrase_matches.append({
            "value": normalized_phrase,
            "subjectMatches": subject_count,
            "previewMatches": preview_count,
            "matches": total_count,
            "weightMultiplier": 2
        })

    total_matches = sum(
        match["matches"]
        for match in keyword_matches + phrase_matches + critical_phrase_matches
    )

    return {
        "matches": total_matches,
        "weightedMatches": weighted_matches,
        "uniqueMatches": sorted(unique_matches),
        "keywordMatches": keyword_matches,
        "phraseMatches": phrase_matches,
        "criticalPhraseMatches": critical_phrase_matches
    }


def _count_word_matches(text: str, word: str) -> int:
    return sum(
        1 for current_word in text.split()
        if current_word == word
    )


def _count_phrase_matches(text: str, phrase: str) -> int:
    pattern = rf"\b{re.escape(phrase)}\b"

    return len(re.findall(pattern, text))
