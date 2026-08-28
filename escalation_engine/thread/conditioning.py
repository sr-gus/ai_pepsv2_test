"""Build the canonical conversation text consumed by the sentiment model."""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from escalation_engine.thread.extractors import (
    get_message_content,
    parse_received_datetime,
)
from escalation_engine.thread.selectors import (
    ENGINEER_ROLE,
    get_message_role,
    get_non_automatic_messages,
    get_valid_messages,
)


@dataclass(frozen=True)
class ConditionedTranscript:
    """Text and audit metadata produced from one accumulated email thread."""

    text: str
    analyzed_messages: int
    ignored_automatic_messages: int
    included_turns: int
    text_sources: dict[str, int]


def build_sentiment_transcript(
    raw_thread: list[Any],
) -> ConditionedTranscript:
    """
    Convert an accumulated email thread to the model's training format.

    Each non-automatic message contributes only its newly authored content.
    Messages are ordered by ``receivedDateTime`` and rendered as one line per
    turn using the exact ``Customer:`` and ``Support:`` role prefixes present
    in the training dataset. Subjects and email metadata are intentionally
    excluded.
    """
    valid_messages = get_valid_messages(raw_thread)
    analyzed_messages = get_non_automatic_messages(raw_thread)
    ordered_messages = _sort_chronologically(analyzed_messages)
    text_sources: Counter[str] = Counter()
    turns = []

    for message in ordered_messages:
        content = get_message_content(message)
        text_sources[content.source] += 1
        normalized_text = _flatten_message_text(content.text)

        if not normalized_text:
            continue

        role = (
            "Support"
            if get_message_role(message) == ENGINEER_ROLE
            else "Customer"
        )
        turns.append(f"{role}: {normalized_text}")

    return ConditionedTranscript(
        text="\n".join(turns),
        analyzed_messages=len(analyzed_messages),
        ignored_automatic_messages=(
            len(valid_messages) - len(analyzed_messages)
        ),
        included_turns=len(turns),
        text_sources=dict(text_sources),
    )


def _sort_chronologically(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Sort dated messages and preserve input order for equal/missing dates."""
    indexed_messages = list(enumerate(messages))

    def sort_key(item):
        index, message = item
        received = parse_received_datetime(message)

        return (
            received is None,
            received if received is not None else datetime.max,
            index,
        )

    return [
        message
        for _, message in sorted(indexed_messages, key=sort_key)
    ]


def _flatten_message_text(value: str) -> str:
    """Keep each modeled turn on one line, matching the training dataset."""
    return " ".join(value.split())
