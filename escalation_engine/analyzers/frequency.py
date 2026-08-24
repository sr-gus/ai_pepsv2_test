import json
import logging
from typing import Any, Optional
from datetime import datetime, timezone

from escalation_engine.thread.extractors import (
    parse_received_datetime,
)
from escalation_engine.thread.selectors import (
    get_message_role,
    get_valid_messages,
    is_automatic_message,
)

logger = logging.getLogger(__name__)

"""
Frequency analysis for the Escalation Prevention Flag System.
 
This module evaluates communication timing patterns
 
Metrics produced
-----------------
1. Rapid follow-ups   -- bursts of consecutive customer messages sent close
                          together without an engineer reply in between.
2. Ghosted hours       -- how long the most recent unanswered customer
                          message has been waiting for a reply.
3. Auto-reply filter   -- out-of-office / system messages are
                          excluded from every frequency metric.
4. Escalation score    -- a single 0.0-1.0 value combining the above.
5. Escalation trend    -- "increasing" / "decreasing" / "neutral", based on
                          how engineer response times evolve across the
                          thread.
"""

# "Rapid follow-up": N+ customer messages within a short window, with no engineer reply in between. 
RAPID_FOLLOWUP_MIN_MESSAGES = 3
RAPID_FOLLOWUP_WINDOW_HOURS = 2.0
 
# "Unanswered burst": how many customer messages are currently sitting unanswered at the end of the thread. 
UNANSWERED_BURST_MIN_MESSAGES = 2
 
# "Ghosted hours": elapsed time since the last unanswered customer message.
GHOSTED_LOW_HOURS = 4.0
GHOSTED_MEDIUM_HOURS = 24.0
GHOSTED_HIGH_HOURS = 72.0

# Beyond "critical," a thread that's been silently open for a week or more
# is a distinct failure mode worth flagging on its own (e.g. lost/abandoned
# tickets) -- this doesn't change scoring (ghosted_component is still
# capped at CRITICAL_RESPONSE_DELAY_HOURS), it's purely informational.
STALE_THREAD_HOURS = 24.0 * 7  # 168h / 7 days
 
LONG_RESPONSE_DELAY_HOURS = GHOSTED_MEDIUM_HOURS
CRITICAL_RESPONSE_DELAY_HOURS = GHOSTED_HIGH_HOURS
 
# Trend detection: compare the average engineer-response-time in the first
# half of the thread vs. the second half.
TREND_MIN_RESPONSE_SAMPLES = 4  # sample count for FULL-confidence trend signal
TREND_MIN_SAMPLES_FLOOR = 2     # minimum samples needed to compute any trend at all
TREND_CHANGE_RATIO = 1.25       # >=25% slower/faster counts as a trend

# When a customer message has been sitting unanswered past LONG_RESPONSE_DELAY_HOURS,
# the thread is forced to label "increasing" regardless of historical averages (see
# the override in analyze_frequency). This floor scales the trend_signal used in the
# score itself to match that label, ramping from 0 at LONG_RESPONSE_DELAY_HOURS up to
# 1.0 at CRITICAL_RESPONSE_DELAY_HOURS, instead of leaving the score's trend
# component at 0 while the displayed label says "increasing."
GHOSTED_TREND_OVERRIDE_RANGE_HOURS = CRITICAL_RESPONSE_DELAY_HOURS - LONG_RESPONSE_DELAY_HOURS
 
# Score weights (sum to 1.0)
SCORE_WEIGHT_GHOSTED = 0.35
SCORE_WEIGHT_RAPID_FOLLOWUP = 0.30
SCORE_WEIGHT_UNANSWERED = 0.20
SCORE_WEIGHT_TREND = 0.15
 
def _normalize_dt(dt: Optional[datetime]) -> Optional[datetime]:
    """Strip timezone info (converting to UTC first) so all datetimes in
    the thread are comparable"""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt



def _evaluate_customer_run(run: list[datetime]) -> int:
    """Count how many sliding windows of RAPID_FOLLOWUP_MIN_MESSAGES
    consecutive customer messages fall within RAPID_FOLLOWUP_WINDOW_HOURS."""
    if len(run) < RAPID_FOLLOWUP_MIN_MESSAGES:
        return 0
    hits = 0
    for i in range(len(run) - RAPID_FOLLOWUP_MIN_MESSAGES + 1):
        window = run[i:i + RAPID_FOLLOWUP_MIN_MESSAGES]
        span_hours = (window[-1] - window[0]).total_seconds() / 3600
        if span_hours <= RAPID_FOLLOWUP_WINDOW_HOURS:
            hits += 1
    return hits
 
 
def _count_rapid_followups(timestamped: list[tuple[datetime, str, Any]]) -> int:
    """Scan the thread for consecutive customer messages (no engineer reply
    in between) and count rapid-followup bursts within each run."""
    hits = 0
    run: list[datetime] = []
    for dt, role, _ in timestamped:
        if role == "customer":
            run.append(dt)
        else:
            hits += _evaluate_customer_run(run)
            run = []
    hits += _evaluate_customer_run(run)
    return hits
 
 
def _compute_unanswered_and_ghosted(
    timestamped: list[tuple[datetime, str, Any]],
    now: Optional[datetime],
) -> tuple[int, Optional[float]]:
    """Return (count of currently-unanswered trailing customer messages,
    hours since the latest one was sent)."""
    if not timestamped:
        return 0, None
 
    last_engineer_idx = None
    for i in range(len(timestamped) - 1, -1, -1):
        if timestamped[i][1] == "engineer":
            last_engineer_idx = i
            break
 
    tail_start = (last_engineer_idx + 1) if last_engineer_idx is not None else 0
    trailing_customer = [item for item in timestamped[tail_start:] if item[1] == "customer"]
 
    if not trailing_customer:
        return 0, 0.0
 
    reference_now = _normalize_dt(now) or datetime.now(timezone.utc).replace(tzinfo=None)
    last_unanswered_dt = trailing_customer[-1][0]
    ghosted_hours = max((reference_now - last_unanswered_dt).total_seconds() / 3600, 0.0)
    return len(trailing_customer), ghosted_hours
 
def _response_times_hours(timestamped: list[tuple[datetime, str, Any]]) -> list[float]:
    """Pair each customer message with the next engineer reply and return
    the response delays"""
    times: list[float] = []
    pending_since: Optional[datetime] = None
    for dt, role, _ in timestamped:
        if role == "customer":
            if pending_since is None:
                pending_since = dt
        else:
            if pending_since is not None:
                times.append((dt - pending_since).total_seconds() / 3600)
                pending_since = None
    return times
 

def _determine_trend(timestamped: list[tuple[datetime, str, Any]]) -> tuple[str, float]:
    """Compare average engineer response time in the first vs. second half
    of the thread.

    Full confidence (signal used as-is) requires TREND_MIN_RESPONSE_SAMPLES
    pairs. With fewer samples (but at least TREND_MIN_SAMPLES_FLOOR), the
    trend is still computed but scaled down by how little data backs it --
    e.g. 3 samples out of a full-confidence 4 contributes 75% of the signal
    it otherwise would, rather than being discarded to 0.0. Below the floor
    there simply isn't enough data to say anything, so it stays neutral.
    """
    response_times = _response_times_hours(timestamped)
    sample_count = len(response_times)
    if sample_count < TREND_MIN_SAMPLES_FLOOR:
        return "neutral", 0.0
 
    mid = sample_count // 2
    first_half, second_half = response_times[:mid], response_times[mid:]
    avg_first = sum(first_half) / len(first_half)
    avg_second = sum(second_half) / len(second_half)
 
    if avg_first <= 0.01:
        ratio = 1.0 if avg_second <= 0.01 else float("inf")
    else:
        ratio = avg_second / avg_first
 
    confidence = min(sample_count / TREND_MIN_RESPONSE_SAMPLES, 1.0)
 
    if ratio >= TREND_CHANGE_RATIO:
        return "increasing", min(ratio - 1, 1.0) * confidence
    if ratio <= 1 / TREND_CHANGE_RATIO:
        return "decreasing", -min(1 - ratio, 1.0) * confidence
    return "neutral", 0.0
 
def _compute_score(
    *,
    rapid_followup_hits: int,
    unanswered_count: int,
    ghosted_hours: Optional[float],
    trend_signal: float,
) -> float:
    """Weighted, normalized 0.0-1.0 escalation score.
    """
    rapid_component = min(rapid_followup_hits / 2, 1.0) * SCORE_WEIGHT_RAPID_FOLLOWUP
    unanswered_component = (
        min(unanswered_count / UNANSWERED_BURST_MIN_MESSAGES, 1.0) * SCORE_WEIGHT_UNANSWERED
    )
    ghosted_component = (
        0.0
        if ghosted_hours is None
        else min(ghosted_hours / CRITICAL_RESPONSE_DELAY_HOURS, 1.0) * SCORE_WEIGHT_GHOSTED
    )
    # Only a worsening trend adds risk; an improving trend is reflected via the "decreasing" 
    trend_component = max(trend_signal, 0.0) * SCORE_WEIGHT_TREND
 
    score = rapid_component + unanswered_component + ghosted_component + trend_component
    return max(0.0, min(score, 1.0))

def _thread_span_days(timestamped: list[tuple[datetime, str, Any]]) -> Optional[float]:
    if len(timestamped) < 2:
        return None
    span_hours = (timestamped[-1][0] - timestamped[0][0]).total_seconds() / 3600
    return max(span_hours / 24, 1 / 24)  # floor at ~1 hour to avoid divide-by-near-zero


def _extract_messages(raw_thread: Any) -> list[Any]:
    """Normalize whatever shape we're handed into a flat list of Graph
    mail-message dicts.

    Callers may pass:
      1. A bare list of Graph messages (already unwrapped).
      2. The full threadEscalationEngine Azure Function payload, i.e.
         {"uri": ..., "method": "POST", "body": {"thread": [...]}} --
         the message array lives at body.thread, not at the top level.
      3. A raw Graph list response, i.e. {"value": [...]}.
      4. Just the inner {"thread": [...]} dict.
    """
    if raw_thread is None:
        return []

    if isinstance(raw_thread, list):
        return raw_thread

    if isinstance(raw_thread, dict):
        body = raw_thread.get("body")
        if isinstance(body, dict) and isinstance(body.get("thread"), list):
            return body["thread"]

        if isinstance(raw_thread.get("thread"), list):
            return raw_thread["thread"]

        if isinstance(raw_thread.get("value"), list):
            return raw_thread["value"]

        logger.warning(
            "analyze_frequency received a dict payload with no recognizable "
            "message array (looked for body.thread, thread, value); keys=%s",
            list(raw_thread.keys()),
        )
        return []

    logger.warning(
        "analyze_frequency received an unsupported payload type: %s",
        type(raw_thread).__name__,
    )
    return []


def _redacted_payload_shape(raw_thread: Any) -> Any:
    """Return a version of raw_thread safe to log -- never let the Azure
    Function key/code (embedded in the payload's "uri") reach the logs."""
    if isinstance(raw_thread, dict):
        safe = dict(raw_thread)
        if "uri" in safe:
            safe["uri"] = "<redacted>"
        return safe
    return raw_thread


async def analyze_frequency(raw_thread: Any, *, now: Optional[datetime] = None) -> dict[str, Any]:

    logger.info(
        "analyze_frequency received payload. type=%s shape=%s",
        type(raw_thread).__name__,
        _redacted_payload_shape(raw_thread),
    )

    messages = _extract_messages(raw_thread)

    try:
        logger.info(
            "analyze_frequency extracted %s message(s):\n%s",
            len(messages),
            json.dumps(messages, indent=2, default=str),
        )
    except (TypeError, ValueError):
        logger.info(
            "analyze_frequency extracted %s message(s) (not JSON-serializable): %r",
            len(messages),
            messages,
        )

    valid_messages = get_valid_messages(messages)

    timestamped: list[tuple[datetime, str, Any]] = []
    spam_count = 0
    messages_with_timestamp = 0
 
    for message in valid_messages:
        dt = _normalize_dt(parse_received_datetime(message))
        if dt is not None:
            messages_with_timestamp += 1
 
        if is_automatic_message(message):
            spam_count += 1
            continue
 
        if dt is None:
            # Missing timestamp, can't participate in time-based metrics - Skip
            continue
 
        timestamped.append((dt, get_message_role(message), message))
 
    timestamped.sort(key=lambda item: item[0])
 
    customer_events = [item for item in timestamped if item[1] == "customer"]
    engineer_events = [item for item in timestamped if item[1] == "engineer"]
 
    flags: set[str] = set()
 
    rapid_followup_hits = _count_rapid_followups(timestamped)
    if rapid_followup_hits > 0:
        flags.add("rapid_followup")
 
    unanswered_count, ghosted_hours = _compute_unanswered_and_ghosted(timestamped, now)
    if unanswered_count >= UNANSWERED_BURST_MIN_MESSAGES:
        flags.add("multiple_unanswered_messages")
 
    if ghosted_hours is not None:
        if ghosted_hours >= CRITICAL_RESPONSE_DELAY_HOURS:
            flags.add("critical_response_delay")
        elif ghosted_hours >= LONG_RESPONSE_DELAY_HOURS:
            flags.add("long_response_delay")
        if ghosted_hours >= STALE_THREAD_HOURS:
            flags.add("stale_thread")
 
    if spam_count > 0:
        flags.add("auto_reply_detected")
 
    trend_label, trend_signal = _determine_trend(timestamped)
 
    # If the customer currently has unanswered messages sitting past the
    # "long delay" threshold, treat the thread as actively worsening
    # regardless of historical average -- this matches the spec's example
    # of "engineer stops responding" implying an increasing trend.
    #
    # Previously this only reassigned trend_label for display, leaving
    # trend_signal (the value _compute_score actually uses) untouched --
    # so a thread could show label="increasing" while silently scoring
    # trend_component=0. Now the override also floors trend_signal, scaled
    # by how far past the "long delay" threshold the ghost has gone, so the
    # displayed label and the score always agree.
    if unanswered_count > 0 and ghosted_hours is not None and ghosted_hours >= LONG_RESPONSE_DELAY_HOURS:
        trend_label = "increasing"
        override_signal = min(
            (ghosted_hours - LONG_RESPONSE_DELAY_HOURS) / GHOSTED_TREND_OVERRIDE_RANGE_HOURS,
            1.0,
        )
        trend_signal = max(trend_signal, override_signal)
 
    score = _compute_score(
        rapid_followup_hits=rapid_followup_hits,
        unanswered_count=unanswered_count,
        ghosted_hours=ghosted_hours,
        trend_signal=trend_signal,
    )
 
    span_days = _thread_span_days(timestamped)
    messages_per_day = round(len(timestamped) / span_days, 2) if span_days else len(timestamped)
 
    logger.info(
        "Starting frequency analysis. valid_message_count=%s messages_with_timestamp=%s spam_ignored=%s",
        len(valid_messages),
        messages_with_timestamp,
        spam_count,
    )
 
    result = {
        "name": "frequency",
        "score": round(score, 2),
        "label": trend_label,
        "flags": sorted(flags),
        "details": {
            "messagesPerDay": messages_per_day,
            "customerMessages": len(customer_events),
            "engineerMessages": len(engineer_events),
            "unansweredCustomerMessages": unanswered_count,
            "ghostedHours": round(ghosted_hours, 1) if ghosted_hours is not None else 0,
            "ghostedDays": round(ghosted_hours / 24, 1) if ghosted_hours is not None else 0,
            "spamMessagesIgnored": spam_count,
            "messagesWithTimestamp": messages_with_timestamp,
        },
    }
 
    logger.info(
        "Completed frequency analysis. score=%s label=%s flags=%s",
        result["score"],
        result["label"],
        result["flags"],
    )
 
    return result