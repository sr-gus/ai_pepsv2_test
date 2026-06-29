import logging
from typing import Any

from escalation_engine.config import ESCALATION_CONFIG

logger = logging.getLogger(__name__)


def build_notification(decision: dict[str, Any]) -> dict[str, Any]:
    """
    Builds a notification object for Power Automate / Teams routing.
    """
    tier = decision.get("tier")

    if tier == "Tier 1":
        notification_key = "tier_1"
    elif tier == "Tier 2":
        notification_key = "tier_2"
    else:
        notification_key = "exit"

    notification_config = ESCALATION_CONFIG["notifications"][notification_key]

    notification = {
        "shouldNotify": notification_config["shouldNotify"],
        "severity": notification_config["severity"],
        "target": notification_config["target"],
        "title": notification_config["title"],
        "summary": notification_config["summary"],
        "recommendedAction": notification_config["recommendedAction"],
        "tier": decision.get("tier"),
        "action": decision.get("action"),
        "reason": decision.get("reason"),
        "confidence": decision.get("confidence"),
        "explanation": decision.get("explanation", [])
    }

    logger.info(
        "Notification built. should_notify=%s severity=%s target=%s",
        notification["shouldNotify"],
        notification["severity"],
        notification["target"]
    )

    return notification