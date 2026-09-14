import logging
from typing import Any

from escalation_engine.config import ESCALATION_CONFIG

logger = logging.getLogger(__name__)


def build_notification(
    decision: dict[str, Any],
    *,
    case_number: str | None = None,
    engineer_name: str | None = None,
    engineer_email: str | None = None,
) -> dict[str, Any]:
    """
    Builds a notification object for Power Automate / Teams routing.
    """
    tier = decision.get("tier")

    if decision.get("decisionSource") == "missing_tracking_id":
        notification_key = "missing_tracking_id"
    elif decision.get("decisionSource") == "explicit_escalation_request":
        notification_key = "explicit_escalation"
    elif tier == "Tier 1":
        notification_key = "tier_1"
    elif tier == "Tier 2":
        notification_key = "tier_2"
    else:
        notification_key = "exit"

    notification_config = ESCALATION_CONFIG["notifications"][notification_key]

    notification = {
        "caseNumber": case_number,
        "engineerName": engineer_name,
        "engineerEmail": engineer_email,
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
        "routingConfidence": decision.get("routingConfidence"),
        "decisionSource": decision.get("decisionSource"),
        "routingOverride": decision.get("routingOverride", False),
        "escalationRequest": decision.get("escalationRequest"),
        "explanation": decision.get("explanation", [])
    }

    logger.info(
        "Notification built. should_notify=%s severity=%s target=%s",
        notification["shouldNotify"],
        notification["severity"],
        notification["target"]
    )

    return notification
