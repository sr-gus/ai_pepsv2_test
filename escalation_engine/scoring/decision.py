import logging
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

    logger.info(
        "Escalation decision completed. tier=%s action=%s confidence=%s explanation=%s",
        decision["tier"],
        decision["action"],
        decision["confidence"],
        decision["explanation"]
    )

    return decision


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
