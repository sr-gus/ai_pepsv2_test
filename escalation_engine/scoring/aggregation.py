import logging
from typing import Any

from escalation_engine.config import ESCALATION_CONFIG

logger = logging.getLogger(__name__)


def aggregate_results(
    sentimental: dict[str, Any],
    keyword: dict[str, Any],
    frequency: dict[str, Any]
) -> dict[str, Any]:
    """
    Aggregates individual analyzer scores into one final escalation score.
    """
    logger.info("Starting result aggregation.")

    weights = ESCALATION_CONFIG["weights"]
    boost_config = ESCALATION_CONFIG["boosts"]

    base_score = (
        sentimental["score"] * weights["sentimental"] +
        keyword["score"] * weights["keyword"] +
        frequency["score"] * weights["frequency"]
    )

    boosts = 0

    if "keyword_trigger" in keyword.get("flags", []):
        boosts += boost_config["keyword_trigger"]

    if "rapid_followup" in frequency.get("flags", []):
        boosts += boost_config["rapid_followup"]

    if "frustration_detected" in sentimental.get("flags", []):
        boosts += boost_config["frustration_detected"]

    final_score = min(base_score + boosts, 1.0)

    result = {
        "score": round(final_score, 2),
        "baseScore": round(base_score, 2),
        "boost": round(boosts, 2),
        "weights": weights,
        "signals": [sentimental, keyword, frequency]
    }

    logger.info(
        "Completed result aggregation. base_score=%s boost=%s final_score=%s",
        result["baseScore"],
        result["boost"],
        result["score"]
    )

    return result