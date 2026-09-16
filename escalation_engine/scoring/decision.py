import logging
import math
import re
from typing import Any

from escalation_engine.config import ESCALATION_CONFIG

logger = logging.getLogger(__name__)


def decide_escalation(aggregate: dict[str, Any]) -> dict[str, Any]:
    """
    Converts the final escalation score into a routing decision.
    """
    logger.info("Starting escalation decision. score=%s", aggregate["score"])

    score = aggregate["score"]
    tier_config = ESCALATION_CONFIG["tiers"]

    explanation = []

    for signal in aggregate["signals"]:
        if signal.get("flags"):
            explanation.extend(signal["flags"])

    explanation = list(dict.fromkeys(explanation))
    escalation_request = _get_escalation_request(aggregate["signals"])

    if escalation_request and escalation_request.get("tier2Override"):
        kind = escalation_request.get("kind")
        reason = (
            "Explicit hierarchical escalation request"
            if kind == "hierarchical"
            else "Explicit customer escalation request"
        )
        decision = {
            "tier": "Tier 2",
            "action": "Engineer, Supervisor",
            "reason": reason,
            "confidence": score,
            "routingConfidence": 1.0,
            "decisionSource": "explicit_escalation_request",
            "routingOverride": True,
            "minimumTierRule": None,
            "escalationRequest": escalation_request,
            "explanation": explanation
        }

        logger.info(
            "Escalation decision overridden by explicit request. kind=%s target=%s score=%s",
            kind,
            escalation_request.get("requestedTarget"),
            score
        )

        return decision

    if score < tier_config["tier_1_min_score"]:
        decision = {
            "tier": None,
            "action": "exit",
            "reason": "Low escalation score",
            "confidence": score,
            "routingConfidence": score,
            "decisionSource": "aggregate_score",
            "routingOverride": False,
            "escalationRequest": escalation_request,
            "explanation": explanation
        }

    elif score < tier_config["tier_2_min_score"]:
        decision = {
            "tier": "Tier 1",
            "action": "Only Support Engineer",
            "reason": "Moderate escalation risk",
            "confidence": score,
            "routingConfidence": score,
            "decisionSource": "aggregate_score",
            "routingOverride": False,
            "escalationRequest": escalation_request,
            "explanation": explanation
        }

    else:
        decision = {
            "tier": "Tier 2",
            "action": "Engineer, Supervisor",
            "reason": "High escalation risk",
            "confidence": score,
            "routingConfidence": score,
            "decisionSource": "aggregate_score",
            "routingOverride": False,
            "escalationRequest": escalation_request,
            "explanation": explanation
        }

    floor = _minimum_tier_rule(aggregate["signals"])
    decision["minimumTierRule"] = floor
    rank = {None: 0, "Tier 1": 1, "Tier 2": 2}
    if floor and rank[floor["tier"]] > rank[decision["tier"]]:
        decision.update({
            "tier": floor["tier"],
            "action": (
                "Engineer, Supervisor"
                if floor["tier"] == "Tier 2" else "Only Support Engineer"
            ),
            "reason": floor["reason"],
            "decisionSource": floor["name"],
            "routingOverride": True,
            # A rule threshold is not a calibrated probability. Preserve the
            # numeric score just as confidence does, rather than inventing 1.0.
            "routingConfidence": score,
            "explanation": list(dict.fromkeys(explanation + [floor["name"]])),
        })

    logger.info(
        "Escalation decision completed. tier=%s action=%s confidence=%s explanation=%s",
        decision["tier"],
        decision["action"],
        decision["confidence"],
        decision["explanation"]
    )

    return decision


def _signal(signals: list[dict[str, Any]], name: str, position: int) -> dict[str, Any]:
    for signal in signals:
        if signal.get("name") == name:
            return signal
    # Azure ML may return an unnamed object. aggregate_results has a fixed
    # sentimental / keyword / frequency order and preserves that raw response.
    if len(signals) > position and not signals[position].get("name"):
        return signals[position]
    return {}


def _valid_score(signal: dict[str, Any]) -> bool:
    value = signal.get("score")
    return (signal.get("success") is not False
            and isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and 0 <= value <= 1)


def _minimum_tier_rule(signals: list[dict[str, Any]]) -> dict[str, Any] | None:
    config = ESCALATION_CONFIG["tier_floors"]
    if not config["enabled"]:
        return None
    sentiment = _signal(signals, "sentimental", 0)
    if not _valid_score(sentiment) or sentiment["score"] < config["sentimental_min_score"]:
        return None
    if str(sentiment.get("label", "")).lower() in {"positive", "neutral", "positivo", "neutro"}:
        return None
    keyword = _signal(signals, "keyword", 1)
    current = keyword.get("details", {}).get("analyzedMessage", {})
    text = current.get("text", "")
    if (not current.get("isLatestHumanMessage") or not isinstance(text, str)
            or not text.strip() or current.get("resolutionAcknowledged")):
        return None
    # Clear closure messages can lack any topic keyword. Avoid rescuing an old
    # negative thread score on a current, complete acknowledgement of closure.
    if re.fullmatch(
        r"\s*(?:(?:thanks|thank you|gracias)[,.!\s]*)?"
        r"(?:thanks|thank you|gracias|ok(?:ay)?|understood|entendido|"
        r"everything is working(?: as expected)?|please close (?:the )?(?:case|ticket)|"
        r"(?:ya )?(?:se resolvi[oó]|est[aá] resuelt[oa])|"
        r"(?:el (?:problema|caso)|la incidencia) (?:ya )?(?:se resolvi[oó]|est[aá] resuelt[oa])|"
        r"(?:todo|ya) funciona(?: correctamente)?)"
        r"[.!\s]*(?:(?:thanks|thank you|gracias)[.!\s]*)?",
        text, re.IGNORECASE,
    ):
        return None

    frequency = _signal(signals, "frequency", 2)
    unanswered = frequency.get("details", {}).get("unansweredCustomerMessages", 0)
    pending = (
        isinstance(unanswered, (int, float))
        and not isinstance(unanswered, bool)
        and math.isfinite(unanswered) and unanswered > 0
    )
    flags = set(frequency.get("flags", []))
    corroborated = pending and (
        unanswered >= 2 or bool(flags & {"long_response_delay", "critical_response_delay"})
    )
    tier_two = (_valid_score(frequency) and frequency["score"] >= config["frequency_min_score"]
                and corroborated)
    return {
        "name": "sentiment_frequency_floor" if tier_two else "high_sentiment_floor",
        "tier": "Tier 2" if tier_two else "Tier 1",
        "reason": ("High sentiment risk with current unanswered customer messages"
                   if tier_two else "High sentiment risk with a current customer message"),
        "sentimentalScore": sentiment["score"],
        "sentimentalThreshold": config["sentimental_min_score"],
        "frequencyScore": frequency.get("score"),
        "frequencyThreshold": config["frequency_min_score"],
        "unansweredCustomerMessages": unanswered,
    }


def _get_escalation_request(signals: list[dict[str, Any]]) -> dict[str, Any] | None:
    for signal in signals:
        if signal.get("name") != "keyword":
            continue

        request = signal.get("details", {}).get("escalationRequest")

        if (
            isinstance(request, dict)
            and request.get("status") != "none"
        ):
            return request

    return None
