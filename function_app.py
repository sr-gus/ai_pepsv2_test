import azure.functions as func
import logging
import json
import asyncio
import re
from datetime import datetime

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

logger = logging.getLogger(__name__)


# =========================================
# ESCALATION CONFIGURATION
# =========================================

ESCALATION_CONFIG = {
    "topics": {
        "billing_issue": {
            "keywords": ["invoice", "billing", "charge", "refund"],
            "threshold": 3
        },
        "technical_failure": {
            "keywords": ["error", "failure", "bug", "issue", "down"],
            "threshold": 2
        },
        "urgent_request": {
            "keywords": ["urgent", "asap", "immediately", "critical"],
            "threshold": 2
        }
    },
    "weights": {
        "sentimental": 0.4,
        "keyword": 0.3,
        "frequency": 0.3
    },
    "boosts": {
        "keyword_trigger": 0.05,
        "rapid_followup": 0.05,
        "frustration_detected": 0.05
    },
    "tiers": {
        "tier_1_min_score": 0.5,
        "tier_2_min_score": 0.75
    },
    "notifications": {
        "exit": {
            "shouldNotify": False,
            "severity": "none",
            "target": None,
            "title": "No escalation required",
            "summary": "Thread did not reach the minimum escalation score.",
            "recommendedAction": "No action required"
        },
        "tier_1": {
            "shouldNotify": True,
            "severity": "medium",
            "target": "support",
            "title": "Tier 1 escalation",
            "summary": "Thread reached moderate escalation risk.",
            "recommendedAction": "Review by support engineer"
        },
        "tier_2": {
            "shouldNotify": True,
            "severity": "high",
            "target": "supervisor",
            "title": "Tier 2 escalation required",
            "summary": "Thread reached high escalation risk.",
            "recommendedAction": "Review by engineer and supervisor"
        }
    }
}


# =========================================
# HELPERS
# =========================================

def normalize_text(thread):
    """
    Full-thread normalizer.
    Useful for sentiment/frequency/other future analyses.
    """
    text = " ".join(
        ((msg.get("subject") or "") + " " + (msg.get("preview") or ""))
        for msg in thread
    )

    return re.sub(r"[^\w\s]", " ", text.lower())


def get_latest_message(thread):
    """
    Returns the newest message in the normalized thread list.
    Expects items shaped like:
    {
        "subject": ...,
        "preview": ...,
        "from": ...,
        "received": ...
    }
    """
    valid_messages = [
        msg for msg in thread
        if isinstance(msg, dict) and msg.get("received")
    ]

    if not valid_messages:
        logger.warning(
            "No messages with received timestamp found. Falling back to last message in thread."
        )
        return thread[-1] if thread else {}

    def parse_dt(value):
        if not value:
            return datetime.min
        try:
            # Handles values like: 2026-05-17T10:00:00Z
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            logger.warning("Unable to parse message received timestamp: %s", value)
            return datetime.min

    latest_message = max(valid_messages, key=lambda m: parse_dt(m.get("received")))

    logger.info(
        "Latest message selected for keyword analysis. received=%s from=%s",
        latest_message.get("received"),
        latest_message.get("from")
    )

    return latest_message


def build_notification(decision):
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


# =========================================
# ANALYSIS FUNCTIONS (STANDARD FORMAT)
# =========================================

async def analyze_sentimental(thread):
    """
    Placeholder sentimental analysis.
    Can later use normalize_text(thread) or the full thread directly.
    """
    logger.info("Starting sentimental analysis. message_count=%s", len(thread))

    result = {
        "name": "sentimental",
        "score": 0.82,
        "label": "negative",
        "confidence": 0.9,
        "flags": ["frustration_detected"],
        "details": {}
    }

    logger.info(
        "Completed sentimental analysis. score=%s label=%s flags=%s",
        result["score"],
        result["label"],
        result["flags"]
    )

    return result


async def analyze_keywords(thread):
    """
    Topic-based keyword analysis.
    Uses ONLY the newest message in the thread.
    If at least one topic exceeds its threshold, keyword_trigger is raised.
    """
    logger.info("Starting keyword analysis. message_count=%s", len(thread))

    latest_msg = get_latest_message(thread)

    # Analyze only newest message
    text = (
        (latest_msg.get("subject") or "") + " " +
        (latest_msg.get("preview") or "")
    )

    text = re.sub(r"[^\w\s]", " ", text.lower())
    words = text.split()

    topic_results = []
    triggered_topics = []
    total_matches = 0

    topic_config = ESCALATION_CONFIG["topics"]

    for topic, config in topic_config.items():
        keyword_matches = 0

        for keyword in config["keywords"]:
            keyword_matches += sum(1 for w in words if w == keyword.lower())

        threshold = config["threshold"]
        triggered = keyword_matches >= threshold

        topic_result = {
            "topic": topic,
            "matches": keyword_matches,
            "threshold": threshold,
            "triggered": triggered
        }

        topic_results.append(topic_result)
        total_matches += keyword_matches

        if triggered:
            triggered_topics.append(topic)

    # OR-condition trigger: if at least one topic triggered
    overall_trigger = len(triggered_topics) > 0

    # Score based only on latest message density
    word_count = max(len(words), 1)
    raw_score = total_matches / word_count
    score = min(raw_score * 5, 1.0)

    # Label
    if overall_trigger:
        label = "triggered"
    elif score > 0.5:
        label = "moderate_signal"
    else:
        label = "low_signal"

    # Flags
    flags = []

    if overall_trigger:
        flags.append("keyword_trigger")

    if total_matches > 5:
        flags.append("high_keyword_density")

    result = {
        "name": "keyword",
        "score": round(score, 2),
        "label": label,
        "flags": flags,
        "details": {
            "analyzedMessage": {
                "received": latest_msg.get("received"),
                "subject": latest_msg.get("subject"),
                "preview": latest_msg.get("preview"),
                "from": latest_msg.get("from")
            },
            "topics": topic_results,
            "triggeredTopics": triggered_topics,
            "totalMatches": total_matches,
            "wordCount": len(words)
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


async def analyze_frequency(thread):
    """
    Placeholder frequency analysis.
    Can later use received timestamps across full thread.
    """
    logger.info("Starting frequency analysis. message_count=%s", len(thread))

    result = {
        "name": "frequency",
        "score": 0.6,
        "label": "increasing",
        "flags": ["rapid_followup"],
        "details": {
            "messagesPerDay": len(thread),
            "ghostedHours": 24
        }
    }

    logger.info(
        "Completed frequency analysis. score=%s label=%s flags=%s",
        result["score"],
        result["label"],
        result["flags"]
    )

    return result


# =========================================
# AGGREGATION (DETERMINANT LOGIC)
# =========================================

def aggregate_results(sentimental, keyword, frequency):
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


# =========================================
# FINAL DECISION (TIER LOGIC)
# =========================================

def decide_escalation(aggregate):
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


# =========================================
# MAIN FUNCTION
# =========================================

@app.route(route="threadEscalationEngine")
async def threadEscalationEngine(req: func.HttpRequest) -> func.HttpResponse:
    logger.info("Thread escalation request received.")

    # ----------------------------
    # 1. VALIDATION
    # ----------------------------
    try:
        req_body = req.get_json()
    except ValueError:
        logger.warning("Request validation failed. Invalid JSON payload.")

        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON payload"}),
            status_code=400,
            mimetype="application/json"
        )

    thread = req_body.get("thread")

    if not isinstance(thread, list) or len(thread) == 0:
        logger.warning(
            "Request validation failed. 'thread' must be a non-empty array. received_type=%s",
            type(thread).__name__
        )

        return func.HttpResponse(
            json.dumps({"error": "'thread' must be a non-empty array"}),
            status_code=400,
            mimetype="application/json"
        )

    logger.info("Request validation completed. raw_thread_count=%s", len(thread))

    # ----------------------------
    # 2. NORMALIZATION
    # ----------------------------
    messages = []
    skipped_messages = 0

    for msg in thread:
        if not isinstance(msg, dict):
            skipped_messages += 1
            continue

        messages.append({
            "subject": msg.get("subject"),
            "preview": msg.get("bodyPreview"),
            "from": msg.get("from", {}).get("emailAddress", {}).get("address"),
            "received": msg.get("receivedDateTime")
        })

    if len(messages) == 0:
        logger.warning(
            "Thread normalization failed. No valid messages found. skipped_messages=%s",
            skipped_messages
        )

        return func.HttpResponse(
            json.dumps({"error": "Thread contains no valid messages"}),
            status_code=400,
            mimetype="application/json"
        )

    logger.info(
        "Thread normalization completed. normalized_message_count=%s skipped_messages=%s",
        len(messages),
        skipped_messages
    )

    # ----------------------------
    # 3. PARALLEL ANALYSIS
    # ----------------------------
    try:
        logger.info("Starting parallel analysis.")

        sentimental, keyword, frequency = await asyncio.wait_for(
            asyncio.gather(
                analyze_sentimental(messages),
                analyze_keywords(messages),
                analyze_frequency(messages)
            ),
            timeout=10
        )

        logger.info("Parallel analysis completed.")

    except asyncio.TimeoutError:
        logger.error("Analysis timeout after 10 seconds.")

        return func.HttpResponse(
            json.dumps({"error": "Analysis timeout"}),
            status_code=504,
            mimetype="application/json"
        )

    except Exception as e:
        logger.exception("Unexpected error during analysis.")

        return func.HttpResponse(
            json.dumps({
                "error": "Internal analysis failure",
                "details": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )

    # ----------------------------
    # 4. AGGREGATION
    # ----------------------------
    aggregate = aggregate_results(sentimental, keyword, frequency)

    # ----------------------------
    # 5. DECISION
    # ----------------------------
    decision = decide_escalation(aggregate)

    # ----------------------------
    # 6. NOTIFICATION
    # ----------------------------
    notification = build_notification(decision)

    # ----------------------------
    # 7. FINAL RESPONSE
    # ----------------------------
    response = {
        "messageCount": len(messages),
        "analysis": {
            "sentimental": sentimental,
            "keyword": keyword,
            "frequency": frequency
        },
        "aggregation": aggregate,
        "decision": decision,
        "notification": notification
    }

    logger.info(
        "Thread escalation request completed. message_count=%s final_score=%s tier=%s action=%s should_notify=%s severity=%s target=%s",
        len(messages),
        aggregate["score"],
        decision["tier"],
        decision["action"],
        notification["shouldNotify"],
        notification["severity"],
        notification["target"]
    )

    return func.HttpResponse(
        json.dumps(response),
        status_code=200,
        mimetype="application/json"
    )