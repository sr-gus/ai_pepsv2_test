import logging
import re
import unicodedata
from typing import Any

from escalation_engine.config import ESCALATION_CONFIG
from escalation_engine.thread.extractors import (
    get_message_content,
    get_preview,
    get_received_datetime,
    get_sender_address,
    get_subject,
)
from escalation_engine.thread.selectors import (
    get_customer_messages,
    get_latest_message,
    get_non_automatic_messages,
    get_valid_messages,
)

logger = logging.getLogger(__name__)

_REPLY_SUBJECT_PATTERN = re.compile(
    r"^\s*(?:re|fw|fwd|aw|sv|rv|res|enc)(?:\[\d+\])?\s*:",
    re.IGNORECASE
)
_NEGATION_WORDS = {
    "neither", "never", "no", "not", "nunca", "sin", "without"
}
_RESOLUTION_PREFIX_WORDS = {
    "aprobada", "aprobado", "completed", "completada", "completado",
    "corregida", "corregido", "fixed", "resolved", "resuelta", "resuelto",
    "successful", "successfully"
}
_RESOLUTION_SUFFIXES = (
    ("ruled", "out"),
    ("was", "ruled", "out"),
    ("is", "no", "longer"),
    ("was", "not", "found"),
    ("did", "not", "occur"),
    ("has", "posted"),
    ("is", "resolved"),
    ("was", "resolved"),
    ("is", "fixed"),
    ("was", "fixed"),
    ("has", "been", "fixed"),
    ("was", "approved"),
    ("has", "been", "resolved"),
    ("is", "working"),
    ("completed", "successfully"),
    ("approved",),
    ("ya", "fue", "resuelto"),
    ("ya", "fue", "resuelta"),
    ("fue", "resuelto"),
    ("fue", "resuelta"),
    ("fue", "aprobado"),
    ("fue", "aprobada"),
    ("se", "resolvio"),
    ("ya", "funciona"),
)
_RESOLUTION_WITHIN_CLAUSE_PATTERN = re.compile(
    r"^(?:\w+\s+){0,3}(?:ya\s+)?(?:"
    r"(?:was|is)\s+(?:approved|fixed|resolved)|"
    r"has\s+been\s+(?:approved|fixed|resolved)|"
    r"fue\s+(?:aprobada|aprobado|corregida|corregido|resuelta|resuelto)|"
    r"se\s+resolvio"
    r")\b"
)
_RESOLUTION_ACKNOWLEDGEMENT_PATTERNS = (
    re.compile(
        r"^\s*(?:thank\s+you|thanks|(?:i\s+)?appreciate).{0,260}\b(?:"
        r"done|resolved|resolving|fixed|approved|active|working|completed|"
        r"handled|reactivated|reactivation|decision|helps|helped"
        r")\b",
        re.DOTALL
    ),
    re.compile(
        r"^\s*i\s+(?:have|ve)\s+received\b.{0,140}\b(?:is|are)\s+now\s+"
        r"(?:showing|working)\s+correctly\b",
        re.DOTALL
    ),
    re.compile(
        r"^\s*(?:the\s+)?(?:refund|credit|payment|hold)\s+has\s+posted\b"
    ),
    re.compile(
        r"^\s*(?:(?:the|this|my|our)\s+)?(?:transfer|refund|issue|question|"
        r"request|hold|subscription|service)\s+(?:(?:has|had|is|was|been|"
        r"finally|now|just|fully|successfully)\s+){0,5}(?:completed|resolved|"
        r"approved|posted|working|reactivated|active)\b",
        re.DOTALL
    ),
    re.compile(
        r"^.{0,120}\b(?:this\s+has\s+(?:been\s+)?resolved|"
        r"this\s+resolved\s+(?:my|our|the)\b)",
        re.DOTALL
    ),
    re.compile(
        r"^\s*(?:confirmed\s*,?\s*)?(?:we\s+re|we\s+are|it\s+is|it\s+s)\s+"
        r"back\s+up\b"
    ),
)
_RESOLUTION_SUPPRESSED_TOPICS = {
    "billing_issue",
    "technical_failure",
    "subscription_state",
    "quota_capacity",
    "transfer_ownership",
    "support_breakdown",
}
_PREVENTIVE_CONTEXT_PATTERN = re.compile(
    r"\b(?:before|avoid|avoiding|prevent|preventing|in\s+case|"
    r"so\s+(?:it|this)\s+(?:doesn\s+t|does\s+not))\b[^.!?]{0,100}$"
)


async def analyze_keywords(raw_thread: list[Any]) -> dict[str, Any]:
    """
    Analyze escalation language in the newest customer message.

    An existing thread keeps its original subject, so subject-only matches are
    reported but are not treated as fresh evidence. Evidence is based on
    distinct signals, not raw repetition.
    """
    logger.info("Starting keyword analysis. raw_thread_count=%s", len(raw_thread))

    valid_messages = get_valid_messages(raw_thread)
    non_automatic_messages = get_non_automatic_messages(raw_thread)
    customer_messages = get_customer_messages(raw_thread)
    ignored_automatic_messages = len(valid_messages) - len(non_automatic_messages)
    ignored_engineer_messages = (
        len(non_automatic_messages) - len(customer_messages)
    )

    logger.info(
        "Keyword analysis filtered messages. customer_message_count=%s ignored_engineer_message_count=%s ignored_automatic_message_count=%s",
        len(customer_messages),
        ignored_engineer_messages,
        ignored_automatic_messages
    )

    latest_msg = get_latest_message(customer_messages)
    message_content = get_message_content(latest_msg)
    raw_subject = get_subject(latest_msg)
    subject_text = _normalize_text(raw_subject)
    content_text = _normalize_text(message_content.text)
    text = _normalize_text(f"{raw_subject} {message_content.text}".strip())
    words = text.split()
    resolution_acknowledged = _acknowledges_resolution(content_text)
    subject_evidence_ignored = (
        len(customer_messages) > 1 or _is_reply_subject(raw_subject)
    )

    topic_results = []
    triggered_topics = []
    total_matches = 0

    topic_config = ESCALATION_CONFIG["topics"]

    for topic, config in topic_config.items():
        topic_match = _analyze_topic_matches(
            subject_text,
            content_text,
            config,
            include_subject_evidence=not subject_evidence_ignored
        )

        threshold = config["threshold"]
        suppressed_by_resolution = (
            resolution_acknowledged and topic in _RESOLUTION_SUPPRESSED_TOPICS
        )
        weighted_matches = (
            0 if suppressed_by_resolution else topic_match["weightedMatches"]
        )
        triggered = weighted_matches >= threshold

        topic_result = {
            "topic": topic,
            "matches": topic_match["matches"],
            "weightedMatches": weighted_matches,
            "rawWeightedMatches": topic_match["weightedMatches"],
            "uniqueMatches": topic_match["uniqueMatches"],
            "keywordMatches": topic_match["keywordMatches"],
            "phraseMatches": topic_match["phraseMatches"],
            "criticalPhraseMatches": topic_match["criticalPhraseMatches"],
            "patternMatches": topic_match["patternMatches"],
            "criticalPatternMatches": topic_match["criticalPatternMatches"],
            "threshold": threshold,
            "suppressedByResolution": suppressed_by_resolution,
            "triggered": triggered
        }

        topic_results.append(topic_result)
        total_matches += topic_match["matches"]

        if triggered:
            triggered_topics.append(topic)

    overall_trigger = len(triggered_topics) > 0
    weighted_total_matches = sum(
        topic["weightedMatches"]
        for topic in topic_results
    )
    total_unique_matches = len({
        match
        for topic in topic_results
        for match in topic["uniqueMatches"]
    })

    # A triggered topic contributes at most 0.5. Independent topics increase
    # confidence more than piling extra vocabulary onto a single topic.
    topic_strengths = sorted((
        min(topic["weightedMatches"] / topic["threshold"], 1.0)
        for topic in topic_results
        if topic["weightedMatches"] > 0
    ), reverse=True)

    if topic_strengths:
        primary_strength = topic_strengths[0]
        secondary_strength = sum(min(strength, 1.0) for strength in topic_strengths[1:])
        score = min(primary_strength * 0.5 + secondary_strength * 0.15, 1.0)
    else:
        score = 0.0

    if overall_trigger:
        label = "triggered"
    elif score > 0.5:
        label = "moderate_signal"
    else:
        label = "low_signal"

    flags = []

    if overall_trigger:
        flags.append("keyword_trigger")

    if weighted_total_matches >= 6:
        flags.append("high_keyword_density")

    result = {
        "name": "keyword",
        "score": round(score, 2),
        "label": label,
        "flags": flags,
        "details": {
            "analyzedMessage": {
                "received": get_received_datetime(latest_msg),
                "subject": raw_subject,
                "preview": get_preview(latest_msg),
                "text": message_content.text,
                "textSource": message_content.source,
                "quotedContentRemoved": message_content.quoted_content_removed,
                "signatureRemoved": message_content.signature_removed,
                "resolutionAcknowledged": resolution_acknowledged,
                "from": get_sender_address(latest_msg),
                "subjectEvidenceIgnored": subject_evidence_ignored
            },
            "topics": topic_results,
            "triggeredTopics": triggered_topics,
            "totalMatches": total_matches,
            "weightedTotalMatches": weighted_total_matches,
            "totalUniqueMatches": total_unique_matches,
            "wordCount": len(words),
            "customerMessageCount": len(customer_messages),
            "ignoredEngineerMessageCount": ignored_engineer_messages,
            "ignoredAutomaticMessageCount": ignored_automatic_messages
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
    decomposed = unicodedata.normalize("NFKD", value.lower())
    without_accents = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )

    return re.sub(r"[^\w\s,.;:!?]", " ", without_accents)


def _is_reply_subject(subject: str) -> bool:
    return bool(_REPLY_SUBJECT_PATTERN.match(subject))


def _acknowledges_resolution(content_text: str) -> bool:
    return any(
        pattern.search(content_text)
        for pattern in _RESOLUTION_ACKNOWLEDGEMENT_PATTERNS
    )


def _analyze_topic_matches(
    subject_text: str,
    content_text: str,
    config: dict[str, Any],
    *,
    include_subject_evidence: bool = True
) -> dict[str, Any]:
    keyword_matches = []
    phrase_matches = []
    critical_phrase_matches = []
    pattern_matches = []
    critical_pattern_matches = []
    candidates = []
    threshold = config["threshold"]

    def add_match(
        collection: list[dict[str, Any]],
        value: str,
        subject_spans: list[tuple[int, int]],
        content_spans: list[tuple[int, int]],
        *,
        priority: int,
        weight: int,
        weight_multiplier: int | None = None
    ) -> None:
        subject_count = len(subject_spans)
        content_count = len(content_spans)
        total_count = subject_count + content_count

        if total_count == 0:
            return

        match = {
            "value": value,
            "subjectMatches": subject_count,
            "contentMatches": content_count,
            # Retained as a compatibility alias for existing consumers. The
            # evidence may now come from uniqueBody/body, not bodyPreview.
            "previewMatches": content_count,
            "matches": total_count
        }

        if weight_multiplier is not None:
            match["weightMultiplier"] = weight_multiplier

        collection.append(match)

        if content_spans:
            source = "content"
            evidence_spans = content_spans
        elif include_subject_evidence and subject_spans:
            source = "subject"
            evidence_spans = subject_spans
        else:
            return

        candidates.append({
            "value": value,
            "source": source,
            "spans": evidence_spans,
            "priority": priority,
            "weight": weight,
            "length": max(end - start for start, end in evidence_spans)
        })

    for keyword in config.get("keywords", []):
        normalized_keyword = _normalize_text(keyword).strip()

        if not normalized_keyword:
            continue

        add_match(
            keyword_matches,
            normalized_keyword,
            _find_literal_matches(subject_text, normalized_keyword),
            _find_literal_matches(content_text, normalized_keyword),
            priority=1,
            weight=1
        )

    for phrase in config.get("phrases", []):
        normalized_phrase = _normalize_text(phrase).strip()

        if not normalized_phrase:
            continue

        add_match(
            phrase_matches,
            normalized_phrase,
            _find_literal_matches(subject_text, normalized_phrase),
            _find_literal_matches(content_text, normalized_phrase),
            priority=2,
            weight=1
        )

    for pattern in config.get("patterns", []):
        add_match(
            pattern_matches,
            pattern["value"],
            _find_pattern_matches(subject_text, pattern["pattern"]),
            _find_pattern_matches(content_text, pattern["pattern"]),
            priority=2,
            weight=pattern.get("weight", 1)
        )

    for phrase in config.get("critical_phrases", []):
        normalized_phrase = _normalize_text(phrase).strip()

        if not normalized_phrase:
            continue

        critical_weight = max(2, threshold)
        add_match(
            critical_phrase_matches,
            normalized_phrase,
            _find_literal_matches(subject_text, normalized_phrase),
            _find_literal_matches(content_text, normalized_phrase),
            priority=3,
            weight=critical_weight,
            weight_multiplier=critical_weight
        )

    for pattern in config.get("critical_patterns", []):
        weight = pattern.get("weight", max(2, threshold))
        add_match(
            critical_pattern_matches,
            pattern["value"],
            _find_pattern_matches(subject_text, pattern["pattern"]),
            _find_pattern_matches(content_text, pattern["pattern"]),
            priority=3,
            weight=weight,
            weight_multiplier=weight
        )

    weighted_matches, unique_matches = _select_distinct_evidence(candidates)
    all_matches = (
        keyword_matches +
        phrase_matches +
        critical_phrase_matches +
        pattern_matches +
        critical_pattern_matches
    )

    return {
        "matches": sum(match["matches"] for match in all_matches),
        "weightedMatches": weighted_matches,
        "uniqueMatches": sorted(unique_matches),
        "keywordMatches": keyword_matches,
        "phraseMatches": phrase_matches,
        "criticalPhraseMatches": critical_phrase_matches,
        "patternMatches": pattern_matches,
        "criticalPatternMatches": critical_pattern_matches
    }


def _select_distinct_evidence(
    candidates: list[dict[str, Any]]
) -> tuple[int, set[str]]:
    selected_spans: dict[str, list[tuple[int, int]]] = {
        "subject": [],
        "content": []
    }
    weighted_matches = 0
    unique_matches = set()

    ordered_candidates = sorted(
        candidates,
        key=lambda candidate: (
            candidate["priority"],
            candidate["length"],
            candidate["weight"]
        ),
        reverse=True
    )

    for candidate in ordered_candidates:
        occupied = selected_spans[candidate["source"]]
        distinct_spans = [
            span for span in candidate["spans"]
            if not any(_spans_overlap(span, selected) for selected in occupied)
        ]

        if not distinct_spans:
            continue

        weighted_matches += candidate["weight"]
        unique_matches.add(candidate["value"])
        occupied.extend(distinct_spans)

    return weighted_matches, unique_matches


def _spans_overlap(
    left: tuple[int, int],
    right: tuple[int, int]
) -> bool:
    return left[0] < right[1] and right[0] < left[1]


def _find_literal_matches(text: str, value: str) -> list[tuple[int, int]]:
    pattern = rf"\b{re.escape(value)}\b"

    return _find_pattern_matches(text, pattern)


def _find_pattern_matches(text: str, pattern: str) -> list[tuple[int, int]]:
    return [
        match.span()
        for match in re.finditer(pattern, text)
        if not _is_negated_or_resolved(text, *match.span())
    ]


def _is_negated_or_resolved(text: str, start: int, end: int) -> bool:
    broader_prefix = text[max(0, start - 120):start]

    if _PREVENTIVE_CONTEXT_PATTERN.search(broader_prefix):
        return True

    prefix_clause = re.split(
        r"(?:[,.;:!?]|\b(?:and|but|or|y|pero|o)\b)",
        text[:start]
    )[-1]
    prefix_words = prefix_clause.split()[-5:]

    if any(word in _NEGATION_WORDS for word in prefix_words[-3:]):
        return True

    local_resolution_start = max(0, len(prefix_words) - 3)

    for index in range(local_resolution_start, len(prefix_words)):
        word = prefix_words[index]

        if word not in _RESOLUTION_PREFIX_WORDS:
            continue

        preceding_words = prefix_words[max(0, index - 2):index]

        if not any(word in _NEGATION_WORDS for word in preceding_words):
            return True

    suffix_clause = re.split(
        r"(?:[,.;:!?]|\b(?:and|but|or|y|pero|o)\b)",
        text[end:]
    )[0].strip()
    suffix_words = suffix_clause.split()[:5]

    if any(
        suffix_words[:len(suffix)] == list(suffix)
        for suffix in _RESOLUTION_SUFFIXES
    ):
        return True

    return bool(_RESOLUTION_WITHIN_CLAUSE_PATTERN.match(suffix_clause))
