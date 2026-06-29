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

    if score < tier_config["tier_1_min_score"]:
        decision = {
            "tier": None,
            "action": "exit",
            "reason": "Low escalation score",
            "confidence": score,
            "explanation": explanation
        }

    elif score < tier_config["tier_2_min_score"]:
        decision = {
            "tier": "Tier 1",
            "action": "Only Support Engineer",
            "reason": "Moderate escalation risk",
            "confidence": score,
            "explanation": explanation
        }

    else:
        decision = {
            "tier": "Tier 2",
            "action": "Engineer, Supervisor",
            "reason": "High escalation risk",
            "confidence": score,
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